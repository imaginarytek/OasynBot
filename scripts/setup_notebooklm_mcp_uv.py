
import json
import os
from pathlib import Path

def update_config():
    config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    print(f"🔧 Analyzing Claude Config at: {config_path}")

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Use absolute path to uvx
    uvx_path = "/Users/wildwood/.local/bin/uvx"

    config["mcpServers"]["notebooklm"] = {
        "command": uvx_path,
        "args": [
            "notebooklm-mcp"
        ]
    }

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Added 'notebooklm' to Claude Desktop Config.")
    print(f"   Command: {uvx_path} notebooklm-mcp")

def main():
    update_config()
    print("\n🎉 Setup Complete!")
    print("⚠️  CRITICAL STEP REQUIRED:")
    print("You must authenticate with NotebookLM before using it.")
    print("Run this command in your terminal:")
    print("   /Users/wildwood/.local/bin/uvx notebooklm-mcp-auth")
    print("\nThis will open a browser. Log in to Google.")
    print("Afterwards, restart Claude Desktop.")

if __name__ == "__main__":
    main()
