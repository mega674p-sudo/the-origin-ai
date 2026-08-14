#!/data/data/com.termux/files/usr/bin/bash
# Start GIGA PHONE AI directly in Termux.
set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -f "config/settings.local.json" ]; then
    printf 'Missing config/settings.local.json. Run: bash setup_termux.sh\n' >&2
    exit 1
fi

if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock
fi

exec python main.py
