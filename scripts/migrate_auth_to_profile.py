import json
import os
from pathlib import Path
from datetime import datetime

storage_dir = Path.home() / ".notebooklm-mcp-cli"
auth_file = storage_dir / "auth.json"
profile_dir = storage_dir / "profiles" / "default"

print(f"Reading from {auth_file}...")

if not auth_file.exists():
    print("Error: auth.json not found")
    exit(1)

with open(auth_file, "r") as f:
    data = json.load(f)

cookies = data.get("cookies", {})
csrf_token = data.get("csrf_token")
session_id = data.get("session_id")
extracted_at_ts = data.get("extracted_at")

if extracted_at_ts:
    last_validated = datetime.fromtimestamp(extracted_at_ts).isoformat()
else:
    last_validated = datetime.now().isoformat()

profile_dir.mkdir(parents=True, exist_ok=True)

# Save cookies.json
cookies_file = profile_dir / "cookies.json"
with open(cookies_file, "w") as f:
    json.dump(cookies, f, indent=2)

# Save metadata.json
metadata = {
    "csrf_token": csrf_token,
    "session_id": session_id,
    "email": None,
    "last_validated": last_validated
}

metadata_file = profile_dir / "metadata.json"
with open(metadata_file, "w") as f:
    json.dump(metadata, f, indent=2)

print(f"✅ Migrated auth data to profile 'default' at {profile_dir}")
