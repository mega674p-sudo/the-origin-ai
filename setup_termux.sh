#!/usr/bin/env bash
# ==============================================================================
# GIGA PHONE AI - Termux Auto-Installer Script
# Author: Senior AI Systems Architect / Giga Agent
# Description: Automates the setup of Ubuntu PRoot, Ollama, Qwen 2.5-Coder 1.5B,
#              and clones the GIGA PHONE AI repository in Termux.
# ==============================================================================

set -e

echo "=== [1/5] Updating Termux packages and installing dependencies ==="
pkg update -y && pkg upgrade -y
pkg install -y proot-distro git curl wget python

echo "=== [2/5] Setting up Ubuntu PRoot Environment ==="
if [ ! -d "$PREFIX/var/lib/proot-distro/installed-rootfs/ubuntu" ]; then
    proot-distro install ubuntu
    echo "Ubuntu PRoot installed successfully."
else
    echo "Ubuntu PRoot is already installed."
fi

echo "=== [3/5] Configuring Ubuntu & Installing Ollama / Python Tools ==="
proot-distro login ubuntu -- bash -c "
    export DEBIAN_FRONTEND=noninteractive
    apt update && apt upgrade -y
    apt install -y curl wget git python3 python3-pip python3-venv zstd build-essential

    # Install Ollama
    if ! command -v ollama &> /dev/null; then
        echo 'Installing Ollama...'
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo 'Ollama already installed.'
    fi
"

echo "=== [4/5] Pulling Qwen2.5-Coder:1.5b Model ==="
echo "Starting Ollama service temporarily to pull model..."
proot-distro login ubuntu -- bash -c "
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
    echo 'Pulling qwen2.5-coder:1.5b (this may take a few minutes depending on connection)...'
    ollama pull qwen2.5-coder:1.5b
    pkill ollama || true
"

echo "=== [5/5] Cloning GIGA PHONE AI Repository ==="
proot-distro login ubuntu -- bash -c "
    cd ~
    if [ -d 'the-origin-ai' ]; then
        cd the-origin-ai
        git pull origin main
    else
        git clone https://github.com/mega674p-sudo/the-origin-ai.git
        cd the-origin-ai
    fi
    pip3 install -r requirements.txt --break-system-packages
"

echo "=============================================================================="
echo " SETUP COMPLETED SUCCESSFULLY!"
echo "=============================================================================="
echo "To start your GIGA PHONE AI inside Ubuntu PRoot, run:"
echo "  proot-distro login ubuntu"
echo "  cd ~/the-origin-ai"
echo "  python3 test_agent.py"
echo "=============================================================================="
