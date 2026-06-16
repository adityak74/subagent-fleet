from __future__ import annotations
import json
from pathlib import Path
from subagent_fleet.config import FleetConfig
from subagent_fleet.generators.common import write_generated

def generate_mcp_config(config: FleetConfig, output_dir: Path, *, source: str = "fleet.yaml", force: bool = False) -> list[Path]:
    if not config.mcp_servers:
        return []
    
    mcp_data = {"mcpServers": {}}
    for name, srv in config.mcp_servers.items():
        mcp_data["mcpServers"][name] = {
            "command": srv.command,
            "args": srv.args,
            "env": srv.env
        }
        
    path = output_dir / "mcp.json"
    content = json.dumps(mcp_data, indent=2) + "\n"
    write_generated(path, content, force=force)
    return [path]
