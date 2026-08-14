#!/data/data/com.termux/files/usr/bin/bash
# Fresh-Termux bootstrap for GIGA PHONE AI. Run with: bash setup_termux.sh
set -euo pipefail

REPO_URL="https://github.com/mega674p-sudo/the-origin-ai.git"
PROJECT_DIR="$HOME/the-origin-ai"

say() {
    printf '\n==> %s\n' "$1"
}

require_value() {
    local prompt="$1"
    local value=""
    while [ -z "$value" ]; do
        read -r -s -p "$prompt" value
        printf '\n'
    done
    printf '%s' "$value"
}

say "Updating Termux and installing lightweight runtime packages"
pkg update -y
pkg upgrade -y
pkg install -y git python python-requests

say "Downloading the GIGA PHONE AI project"
if [ -d "$PROJECT_DIR/.git" ]; then
    git -C "$PROJECT_DIR" pull --ff-only origin main
elif [ -e "$PROJECT_DIR" ]; then
    printf 'Cannot use %s because it already exists and is not a Git repository.\n' "$PROJECT_DIR" >&2
    exit 1
else
    git clone --depth 1 "$REPO_URL" "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

if ! python -c 'import requests' >/dev/null 2>&1; then
    say "Installing the minimal Python dependency"
    python -m pip install --no-cache-dir -r requirements.txt
fi

say "Telegram setup"
GEMINI_API_KEY="$(require_value 'Gemini API key: ')"
TELEGRAM_BOT_TOKEN="$(require_value 'Telegram bot token: ')"
export GEMINI_API_KEY TELEGRAM_BOT_TOKEN

BOT_USERNAME="$(python - <<'PY'
import json
import os
import urllib.request

url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/getMe"
with urllib.request.urlopen(url, timeout=15) as response:
    payload = json.load(response)
if not payload.get("ok") or not payload.get("result", {}).get("username"):
    raise SystemExit("The Telegram bot token was rejected.")
print(payload["result"]["username"])
PY
)"

printf '\nOpen https://t.me/%s, send /start in a private chat, then press Enter here.\n' "$BOT_USERNAME"
read -r _

TELEGRAM_IDENTITY="$(python - <<'PY'
import json
import os
import urllib.parse
import urllib.request

base = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/getUpdates"
query = urllib.parse.urlencode({"timeout": 20})
with urllib.request.urlopen(f"{base}?{query}", timeout=30) as response:
    updates = json.load(response)

for update in reversed(updates.get("result", [])):
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    if chat.get("type") == "private" and chat.get("id") and sender.get("id"):
        print(f"{chat['id']}:{sender['id']}")
        break
else:
    raise SystemExit("No new private /start message was received. Run the installer again and send /start before pressing Enter.")
PY
)"
IFS=':' read -r TELEGRAM_CHAT_ID ALLOWED_USER_ID <<EOF
$TELEGRAM_IDENTITY
EOF

export TELEGRAM_CHAT_ID ALLOWED_USER_ID
python - <<'PY'
import json
import os

path = "config/settings.local.json"
settings = {
    "gemini": {"api_key": os.environ["GEMINI_API_KEY"]},
    "telegram": {
        "bot_token": os.environ["TELEGRAM_BOT_TOKEN"],
        "chat_id": os.environ["TELEGRAM_CHAT_ID"],
        "allowed_user_id": os.environ["ALLOWED_USER_ID"],
    },
}
with open(path, "w", encoding="utf-8") as output:
    json.dump(settings, output, ensure_ascii=False, indent=2)
    output.write("\n")
PY
unset GEMINI_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID ALLOWED_USER_ID
chmod 600 config/settings.local.json

say "Checking the local code before startup"
python -m unittest test_long_polling.py test_self_correction.py test_task_agent.py

if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock
fi

say "Installation complete. Starting GIGA PHONE AI"
exec bash start_giga.sh
