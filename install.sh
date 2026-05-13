#!/usr/bin/env bash
set -euo pipefail

HOOK_SCRIPT="$(cd "$(dirname "$0")" && pwd)/hooks/on_prompt.py"
SETTINGS="$HOME/.claude/settings.json"

# Ensure hook is executable
chmod +x "$HOOK_SCRIPT"

# Create settings file if missing
if [ ! -f "$SETTINGS" ]; then
    echo '{}' > "$SETTINGS"
fi

# Check python available
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found" >&2
    exit 1
fi

# Install dependencies
pip install -q -r "$(dirname "$0")/requirements.txt"

# Inject hook via Python (safe JSON merge, no overwrite of existing settings)
python3 - "$SETTINGS" "$HOOK_SCRIPT" <<'EOF'
import json, sys

settings_path = sys.argv[1]
hook_script = sys.argv[2]

with open(settings_path) as f:
    settings = json.load(f)

hook_entry = {
    "matcher": "",
    "hooks": [{"type": "command", "command": f"python3 {hook_script}"}]
}

hooks = settings.setdefault("hooks", {})
existing = hooks.setdefault("UserPromptSubmit", [])

# Avoid duplicate
if not any(hook_script in str(h) for h in existing):
    existing.append(hook_entry)

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print(f"Hook registered: {hook_script}")
EOF

echo ""
echo "Alfred installed. Restart Claude Code to activate."
echo "DB:       $HOME/alfred_v1/data/alfred.db"
echo "Archives: $HOME/alfred_v1/archives/"
