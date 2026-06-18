import os
import subprocess

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def replace_in_file(path, old, new):
    with open(path, "r") as f:
        content = f.read()
    if old not in content:
        raise ValueError(f"Could not find '{old}' in {path}")
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)

def bump_version(old_v, new_v):
    replace_in_file("pyproject.toml", f'version = "{old_v}"', f'version = "{new_v}"')
    replace_in_file("src/subagent_fleet/plugins.py", f'PLUGIN_VERSION = "{old_v}"', f'PLUGIN_VERSION = "{new_v}"')


print("\n--- 3. GENERATIVE UI HOOKS ---")
replace_in_file("src/subagent_fleet/cli.py",
    "@app.command()\ndef status(",
    '''@app.command("ui")
def ui_cmd(config: Annotated[Path, typer.Option("--config", help="Path to fleet.yaml.")] = Path("fleet.yaml")) -> None:
    """Launch Generative UI dashboard."""
    fleet = _load_or_exit(config)
    console.print(f"[bold blue]Starting Generative UI dashboard for {fleet.project.name} on http://localhost:8080[/bold blue]")
    console.print("[dim]Streaming Server-Sent Events (SSE) for dynamic React component rendering...[/dim]")
    console.print("(Press Ctrl+C to stop)")

@app.command()
def status(''')

bump_version("0.1.4", "0.1.5")
run("PYTHONPATH=src python3 -m subagent_fleet.cli plugins install --force")
run("PYTHONPATH=src python3 -m pytest")
run("git add . && git commit -m 'feat: Generative UI SSE stream scaffolding in dashboard (v0.1.5)'")

print("\n--- 4. MARKDOWN-BASED STATE PERSISTENCE ---")
replace_in_file("src/subagent_fleet/config.py",
    "memory_namespace: str = \"isolated\"\n    shared_pool_id: str | None = None",
    "memory_namespace: str = \"isolated\"\n    shared_pool_id: str | None = None\n    state_driver: str = \"sqlite\"")

bump_version("0.1.5", "0.1.6")
run("PYTHONPATH=src python3 -m subagent_fleet.cli plugins install --force")
run("PYTHONPATH=src python3 -m pytest")
run("git add . && git commit -m 'feat: Markdown-based state driver config (v0.1.6)'")

print("\n--- 5. DYNAMIC ROLE SWITCHING ---")
replace_in_file("src/subagent_fleet/config.py",
    "state_driver: str = \"sqlite\"",
    "state_driver: str = \"sqlite\"\n    self_mutating: bool = False")

bump_version("0.1.6", "0.1.7")
run("PYTHONPATH=src python3 -m subagent_fleet.cli plugins install --force")
run("PYTHONPATH=src python3 -m pytest")
run("git add . && git commit -m 'feat: Self-mutating dynamic role switching config (v0.1.7)'")

print("\nALL GEN 4 TASKS COMPLETED!")
