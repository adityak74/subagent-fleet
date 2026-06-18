from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from subagent_fleet.config import ConfigError, FleetConfig, config_to_plain_dict, load_config
from subagent_fleet.defaults import STARTER_FLEET_YAML
from subagent_fleet.discovery import discovery_to_json, discover_fleet
from subagent_fleet.generators import generate_claude_agents, generate_env_file, generate_litellm_config
from subagent_fleet.plugins import PluginInstallError, install_plugin_marketplaces
from subagent_fleet.skills import (
    ASSISTANT_TARGETS,
    BUNDLED_SKILLS,
    SkillInstallError,
    install_skills,
)
from subagent_fleet.status import get_status, routes_to_json
from subagent_fleet.warmup import warmup_models

app = typer.Typer(help="Run Claude Code-style subagents across your local model fleet.", no_args_is_help=True)
skills_app = typer.Typer(help="Install assistant skills for using subagent-fleet.", no_args_is_help=True)
plugins_app = typer.Typer(help="Install assistant plugin marketplace bundles.", no_args_is_help=True)
app.add_typer(skills_app, name="skills")
app.add_typer(plugins_app, name="plugins")
console = Console()


def _load_or_exit(path: Path) -> FleetConfig:
    try:
        return load_config(path)
    except ConfigError as exc:
        console.print(f"[red]Invalid {path}:[/red]\n\n{exc}")
        raise typer.Exit(1) from exc


@app.command()
def init(
    output: Annotated[Path, typer.Option("--output", help="Path to write the starter fleet config.")] = Path("fleet.yaml"),
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing config file.")] = False,
) -> None:
    """Create a starter fleet.yaml."""
    if output.exists() and not force:
        console.print(f"[red]{output} already exists. Use --force to overwrite.[/red]")
        raise typer.Exit(1)
    output.write_text(STARTER_FLEET_YAML)
    console.print(f"Created {output}")
    console.print("\nEdit it with your Ollama node endpoints, then run:\n")
    console.print("  subagent-fleet discover")
    console.print("  subagent-fleet generate")


@app.command()
def validate(config: Annotated[Path, typer.Option("--config", help="Path to fleet.yaml.")] = Path("fleet.yaml")) -> None:
    """Validate fleet.yaml."""
    fleet = _load_or_exit(config)
    console.print(f"{config} is valid.")
    for warning in fleet.alias_warnings():
        console.print(f"[yellow]Warning:[/yellow] {warning}")


@app.command()
def discover(
    config: Annotated[Path, typer.Option("--config", help="Path to fleet.yaml.")] = Path("fleet.yaml"),
    as_json: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
    write: Annotated[bool, typer.Option("--write", help="Write .subagent-fleet/discovery.json.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show connection errors for offline nodes.")] = False,
) -> None:
    """Discover models available on configured Ollama nodes."""
    fleet = _load_or_exit(config)
    results = discover_fleet(fleet)
    payload = {"fleet": fleet.project.name, "nodes": discovery_to_json(results)}

    if write:
        discovery_path = Path(".subagent-fleet/discovery.json")
        discovery_path.parent.mkdir(parents=True, exist_ok=True)
        discovery_path.write_text(json.dumps(payload, indent=2) + "\n")

    if as_json:
        console.print(json.dumps(payload, indent=2))
        return

    console.print(f"Fleet: {fleet.project.name}\n")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Node")
    table.add_column("Status")
    table.add_column("Models")
    if verbose:
        table.add_column("Error")
    for result in results:
        status = "[green]online[/green]" if result.online else "[red]offline[/red]"
        row = [result.name, status, ", ".join(result.models) if result.models else "-"]
        if verbose:
            row.append(result.error or "")
        table.add_row(*row)
    console.print(table)
    if write:
        console.print(f"\nWrote {discovery_path}")


@app.command()
def generate(
    config: Annotated[Path, typer.Option("--config", help="Path to fleet.yaml.")] = Path("fleet.yaml"),
    out: Annotated[Path, typer.Option("--out", help="Output root.")] = Path("."),
    target: Annotated[
        list[str] | None, 
        typer.Option("--target", "-t", help="Generate configurations for specific targets: claude, aider. Can be repeated. Defaults to claude.")
    ] = None,
    litellm_only: Annotated[bool, typer.Option("--litellm-only", help="Only generate LiteLLM config.")] = False,
    claude_only: Annotated[bool, typer.Option("--claude-only", help="Only generate Claude agent files (deprecated, use --target claude).")] = False,
    force: Annotated[bool, typer.Option("--force", help="Overwrite generated files.")] = False,
) -> None:
    """Generate LiteLLM, Claude Code, and Aider configuration files."""
    if litellm_only and claude_only:
        console.print("[red]Use at most one of --litellm-only or --claude-only.[/red]")
        raise typer.Exit(1)

    targets = [t.lower() for t in (target or [])]
    if claude_only and "claude" not in targets:
        targets.append("claude")
    if not targets:
        targets = ["claude"]

    fleet = _load_or_exit(config)
    source = str(config)
    generated: list[Path] = []
    
    from subagent_fleet.generators.aider import generate_aider_config
    
    try:
        if not claude_only and "claude" in targets and not litellm_only:
            # We generate litellm for both claude and aider if not litellm_only/claude_only
            generated.append(generate_litellm_config(fleet, out / "litellm_config.yaml", source=source, force=force))
        elif "aider" in targets and not litellm_only:
            generated.append(generate_litellm_config(fleet, out / "litellm_config.yaml", source=source, force=force))
        elif litellm_only:
            generated.append(generate_litellm_config(fleet, out / "litellm_config.yaml", source=source, force=force))

        if "claude" in targets and not litellm_only:
            generated.extend(generate_claude_agents(fleet, out / ".claude" / "agents", source=source, force=force))
            generated.append(generate_env_file(fleet, out / ".env.subagent-fleet", source=source, force=force))
            
            from subagent_fleet.generators.mcp import generate_mcp_config
            mcp_paths = generate_mcp_config(fleet, out, source=source, force=force)
            if mcp_paths:
                generated.extend(mcp_paths)
            
            if fleet.project.dynamic_routing:
                from subagent_fleet.generators.router import generate_router_script
                generated.extend(generate_router_script(fleet, out, source=source, force=force))
            
            from subagent_fleet.generators.wol import generate_wol_hook
            generated.extend(generate_wol_hook(fleet, out, source=source, force=force))
            
            from subagent_fleet.generators.security import generate_security_hook
            sec_paths = generate_security_hook(fleet, out, source=source, force=force)
            if sec_paths:
                generated.extend(sec_paths)
            
            from subagent_fleet.generators.blackboard import generate_blackboard_daemon
            bb_paths = generate_blackboard_daemon(fleet, out, source=source, force=force)
            if bb_paths:
                generated.extend(bb_paths)
            
            from subagent_fleet.generators.scheduler import generate_scheduler_hook
            sched_paths = generate_scheduler_hook(fleet, out, source=source, force=force)
            if sched_paths:
                generated.extend(sched_paths)
            
        if "aider" in targets and not litellm_only:
            generated.extend(generate_aider_config(fleet, out, source=source, force=force))
            
    except FileExistsError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    # Remove duplicates from generated list while preserving order
    seen = set()
    generated_unique = []
    for p in generated:
        if p not in seen:
            seen.add(p)
            generated_unique.append(p)
    generated = generated_unique

    console.print("Generated:")
    for path in generated:
        console.print(f"  {path}")
        
    if litellm_only:
        return
        
    console.print("\nStart LiteLLM with:")
    console.print(f"  litellm --config {out / 'litellm_config.yaml'} --host {fleet.project.gateway.host} --port {fleet.project.gateway.port}")
    
    if "claude" in targets:
        console.print("\nThen for Claude Code run:")
        console.print("  source .env.subagent-fleet")
        console.print("  claude")
        
    if "aider" in targets:
        console.print("\nThen for Aider run:")
        console.print("  export OPENAI_API_KEY=ollama")
        console.print(f"  export OPENAI_API_BASE=http://localhost:{fleet.project.gateway.port}/v1")
        console.print("  aider")
        
    for warning in fleet.alias_warnings():
        console.print(f"[yellow]Warning:[/yellow] {warning}")


@app.command()
def warmup(
    config: Annotated[Path, typer.Option("--config", help="Path to fleet.yaml.")] = Path("fleet.yaml"),
    model: Annotated[str | None, typer.Option("--model", help="Only warm this configured model name.")] = None,
    agent: Annotated[str | None, typer.Option("--agent", help="Only warm the model used by this agent.")] = None,
) -> None:
    """Preload configured Ollama models."""
    fleet = _load_or_exit(config)
    try:
        results = warmup_models(fleet, model_name=model, agent_name=agent)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    console.print("Warming models:\n")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Model")
    table.add_column("Node")
    table.add_column("Ollama Model")
    table.add_column("Status")
    for result in results:
        table.add_row(
            result.model_name,
            result.node_name,
            result.ollama_model,
            "[green]ok[/green]" if result.ok else f"[red]failed[/red] {result.error}",
        )
    console.print(table)
    if any(not result.ok for result in results):
        raise typer.Exit(1)


@app.command()
def status(
    config: Annotated[Path, typer.Option("--config", help="Path to fleet.yaml.")] = Path("fleet.yaml"),
    as_json: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    """Show node status and agent routing."""
    fleet = _load_or_exit(config)
    nodes, routes = get_status(fleet)
    if as_json:
        console.print(
            json.dumps(
                {
                    "fleet": fleet.project.name,
                    "nodes": discovery_to_json(nodes),
                    "routes": routes_to_json(routes),
                },
                indent=2,
            )
        )
        return

    console.print(f"Fleet: {fleet.project.name}\n")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Node")
    table.add_column("Status")
    table.add_column("Endpoint")
    table.add_column("Models")
    for node in nodes:
        table.add_row(
            node.name,
            "[green]online[/green]" if node.online else "[red]offline[/red]",
            node.endpoint,
            ", ".join(node.models) if node.models else "-",
        )
    console.print(table)
    _print_routes(routes)


@app.command()
def doctor(config: Annotated[Path, typer.Option("--config", help="Path to fleet.yaml.")] = Path("fleet.yaml")) -> None:
    """Validate config and print local-network security guidance."""
    fleet = _load_or_exit(config)
    console.print(f"{config} is valid.")
    console.print("\nSecurity checks:")
    console.print("- Do not expose Ollama directly to the public internet.")
    console.print("- Do not expose LiteLLM without authentication.")
    console.print("- Prefer LAN, firewall rules, Tailscale, or WireGuard.")
    console.print(f"- Use a non-default {fleet.project.gateway.master_key_env} beyond local dev.")
    console.print("\nOllama worker setup hint:")
    console.print('  launchctl setenv OLLAMA_HOST "0.0.0.0:11434"')
    console.print('  launchctl setenv OLLAMA_KEEP_ALIVE "-1"')
    console.print('  launchctl setenv OLLAMA_NUM_PARALLEL "1"')
    console.print('  launchctl setenv OLLAMA_MAX_LOADED_MODELS "1"')


@app.command()
def clean(out: Annotated[Path, typer.Option("--out", help="Output root to clean.")] = Path("."), force: bool = False) -> None:
    """Remove generated files from an output root."""
    targets = [out / "litellm_config.yaml", out / ".env.subagent-fleet"]
    targets.extend((out / ".claude" / "agents").glob("*.md") if (out / ".claude" / "agents").exists() else [])
    if not force:
        console.print("Files that would be removed:")
        for target in targets:
            console.print(f"  {target}")
        console.print("\nRun with --force to remove them.")
        return
    for target in targets:
        target.unlink(missing_ok=True)
    console.print("Removed generated files.")


@skills_app.command("list")
def list_skills() -> None:
    """List bundled skills and supported assistant targets."""
    skill_table = Table(title="Bundled skills", show_header=True, header_style="bold")
    skill_table.add_column("Skill")
    skill_table.add_column("Description")
    for skill in BUNDLED_SKILLS.values():
        skill_table.add_row(skill.name, skill.description)
    console.print(skill_table)

    target_table = Table(title="Targets", show_header=True, header_style="bold")
    target_table.add_column("Target")
    target_table.add_column("Install Directory")
    target_table.add_column("Description")
    for target in ASSISTANT_TARGETS.values():
        target_table.add_row(target.name, str(target.directory), target.description)
    console.print(target_table)


@skills_app.command("install")
def install_assistant_skills(
    out: Annotated[Path, typer.Option("--out", help="Project root or output directory.")] = Path("."),
    target: Annotated[
        list[str] | None,
        typer.Option("--target", "-t", help="Assistant target: all, claude-code, codex, opencode. Can be repeated or comma-separated."),
    ] = None,
    skill: Annotated[
        list[str] | None,
        typer.Option("--skill", "-s", help="Bundled skill: all, subagent-fleet-setup, subagent-fleet-operations. Can be repeated or comma-separated."),
    ] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing installed skill files.")] = False,
) -> None:
    """Install bundled assistant skills for Claude Code, Codex, OpenCode, or all targets."""
    try:
        results = install_skills(output_root=out, targets=target or ["all"], skills=skill or ["all"], force=force)
    except (FileExistsError, SkillInstallError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    console.print("Installed skills:")
    for result in results:
        console.print(f"  {result.target}: {result.skill} -> {result.path}")


@plugins_app.command("install")
def install_assistant_plugins(
    out: Annotated[Path, typer.Option("--out", help="Marketplace root or output directory.")] = Path("."),
    target: Annotated[
        list[str] | None,
        typer.Option("--target", "-t", help="Plugin target: all, claude-code, codex. Can be repeated or comma-separated."),
    ] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing plugin marketplace files.")] = False,
) -> None:
    """Install Claude Code and Codex plugin marketplace bundles."""
    try:
        results = install_plugin_marketplaces(output_root=out, targets=target or ["all"], force=force)
    except (FileExistsError, PluginInstallError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    console.print("Installed plugin marketplace files:")
    for result in results:
        console.print(f"  {result.target}: {result.path}")
    console.print("\nPlugin skills included:")
    console.print("  subagent-fleet-bootstrap")
    console.print("  subagent-fleet-setup")
    console.print("  subagent-fleet-operations")


@app.command()
def trace(
    log_file: Annotated[Path, typer.Option("--log-file", help="Path to LiteLLM log file to stream.")] = Path("litellm.log"),
) -> None:
    """Stream and format LiteLLM logs to monitor subagent execution."""
    if not log_file.exists():
        console.print(f"[red]Log file {log_file} not found.[/red]")
        console.print("Make sure to start LiteLLM with logging redirected to this file:")
        console.print("  litellm --config litellm_config.yaml --detailed_debug > litellm.log 2>&1")
        raise typer.Exit(1)
        
    console.print(f"[bold blue]Tracking subagent fleet activity from {log_file}...[/bold blue] (Press Ctrl+C to exit)\n")
    
    with open(log_file, "r") as f:
        f.seek(0, 2) # go to end
        try:
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                line = line.strip()
                if not line:
                    continue
                
                if "POST /v1/chat/completions" in line or "POST /chat/completions" in line:
                    console.print(f"[green]→ Chat Request[/green] [dim]{line}[/dim]")
                elif "200 OK" in line:
                    console.print(f"[blue]← 200 OK[/blue] [dim]{line}[/dim]")
                elif "Exception" in line or "Error" in line:
                    console.print(f"[bold red]{line}[/bold red]")
                elif "API Base" in line or "Model:" in line:
                    console.print(f"[bold yellow]⚙ Routing:[/bold yellow] [yellow]{line}[/yellow]")
                elif "litellm" in line.lower():
                    console.print(f"[dim]{line}[/dim]")
                    
        except KeyboardInterrupt:
            console.print("\n[bold]Stopped tracing.[/bold]")


def _print_routes(routes: list[object]) -> None:
    console.print("\nAgent routing:\n")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Agent")
    table.add_column("Node")
    table.add_column("Ollama Model")
    table.add_column("LiteLLM Alias")
    for route in routes:
        table.add_row(route.agent, route.node, route.ollama_model, route.litellm_alias)
    console.print(table)


if __name__ == "__main__":
    app()
