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
printf 'Open your Telegram bot, send it /start, then paste its values below.\n'
GEMINI_API_KEY="$(require_value 'Gemini API key: ')"
TELEGRAM_BOT_TOKEN="$(require_value 'Telegram bot token: ')"
printf 'Telegram chat ID (private chat: usually your numeric user ID): '
read -r TELEGRAM_CHAT_ID
printf 'Allowed Telegram user ID (your numeric user ID): '
read -r ALLOWED_USER_ID

if [ -z "$TELEGRAM_CHAT_ID" ] || [ -z "$ALLOWED_USER_ID" ]; then
    printf 'Chat ID and allowed user ID cannot be empty.\n' >&2
    exit 1
fi

export GEMINI_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID ALLOWED_USER_ID
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
