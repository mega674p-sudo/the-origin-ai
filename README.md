# GIGA PHONE AI

**GIGA PHONE AI** is an advanced autonomous agent designed to operate within resource-constrained mobile Linux environments such as **Termux** on Android and **Ubuntu**. Controlled remotely via a secure **Telegram bot interface**, the agent is engineered for end-to-end task automation, system administration, and workflow orchestration.

---

## Core Architecture & Capabilities

1. **Telegram-Based Remote Control**: 
   - Interacts with users asynchronously through a Telegram bot.
   - Streams real-time status updates, error logs, and execution summaries directly to the operator's chat.

2. **Self-Correction & Resilient Execution**: 
   - Executes system bash commands through a secure subprocess wrapper.
   - Automatically intercepts non-zero exit codes and error logs (stderr), analyzing failures to apply heuristic fixes (such as missing package installation or permission adjustments).

3. **Service Deployment & Workflow Orchestration**: 
   - Automates the deployment and management of background services like **n8n** for workflow automation.
   - Orchestrates automated multimedia production pipelines, including YouTube video generation scripts.

---

## Project Structure

```text
~/Desktop/my_ai_project/
├── config/
│   └── settings.json          # Configuration parameters and bot tokens
├── core/
│   ├── executor.py            # Secure subprocess command execution engine
│   ├── self_corrector.py      # Error analysis and automated fix loop
│   └── notifier.py            # Asynchronous Telegram notification bridge
├── services/
│   ├── n8n_manager.py         # n8n deployment and health monitoring daemon
│   └── yt_pipeline.py         # YouTube video production pipeline automation
├── logs/                      # Execution logs and error traces
├── main.py                    # Main agent entry point and orchestrator
├── requirements.txt           # Python package dependencies
└── README.md                  # Project documentation
```

---

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/mega674p-sudo/the-origin-ai.git
   cd the-origin-ai
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your Telegram Bot token in `config/settings.json`.
4. Run the agent:
   ```bash
   python main.py
   ```
