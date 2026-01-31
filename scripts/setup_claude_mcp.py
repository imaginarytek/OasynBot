
import json
import os
from pathlib import Path

# Config Path
config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
project_path = "/Users/wildwood/Desktop/HedgemonyBot"

print(f"🔧 Analyzing Claude Config at: {config_path}")

# Load existing
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}
except json.JSONDecodeError:
    config = {}

# Ensure mcpServers key exists
if "mcpServers" not in config:
    config["mcpServers"] = {}

# Add HedgemonyBot Filesystem Server
config["mcpServers"]["hedgemony-fs"] = {
    "command": "npx",
    "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        project_path
    ]
}

# Add project to trusted folders (if localAgentModeTrustedFolders exists)
# Note: Newer versions use a different key or handle it via UI, but we'll try to add it.
# Actually, the user's config had 'preferences', let's check.
if "preferences" not in config:
    config["preferences"] = {}

if "localAgentModeTrustedFolders" not in config["preferences"]:
    config["preferences"]["localAgentModeTrustedFolders"] = []

if project_path not in config["preferences"]["localAgentModeTrustedFolders"]:
    config["preferences"]["localAgentModeTrustedFolders"].append(project_path)


# Save back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ SUCCESS: Added 'hedgemony-fs' to Claude Desktop Config.")
print(f"📂 Mapped Path: {project_path}")
print("👉 PLEASE RESTART CLAUDE DESKTOP APP NOW.")
