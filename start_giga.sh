#!/usr/bin/env bash
# ==============================================================================
# GIGA PHONE AI - Mobile Startup Script
# Description: Starts Ollama background service and runs the autonomous agent.
# ==============================================================================

echo "Starting Ollama background service..."
nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 3

echo "Ollama is running. Launching GIGA PHONE AI Agent..."
cd "$(dirname "$0")"
python3 test_agent.py
