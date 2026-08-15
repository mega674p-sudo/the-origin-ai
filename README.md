# GIGA PHONE AI

**GIGA PHONE AI** is a lightweight hybrid coding agent for heavy workloads. The **Redmi 10a is the Telegram control and approval console**, while an always-on **Ubuntu worker** performs code analysis, shell execution, testing, verification, and Git workflows. Gemini supplies remote reasoning; no local LLM is required on the phone.

---

## Core Architecture & Capabilities

The runtime follows a sequential **planner → security reviewer → executor → verifier** pipeline. `/task` creates a bounded plan without executing commands, stores it with a unique task ID, and sends it to Telegram. The operator must reply with the exact `/approve <task-id>` before execution begins. The policy engine runs locally before every shell call and classifies commands as `allow`, `review`, or `deny`.

The Ubuntu worker executes inside a configured project workspace with timeouts and bounded output capture. Failed commands may be sent to Gemini for correction, but every corrected command is checked by the local policy again. Declared read-only verification commands provide concrete evidence after each important step. `/explore` and `/inspect` are read-only paths that cannot execute mutation-sensitive commands.

The worker records a bounded append-only JSONL audit trail and a compact recent-task memory. These records are intentionally capped and redact common token/key formats. Review-sensitive operations such as package installation and Git push are not permitted through direct `/run`; they must be represented in an approved task plan and remain visible in the plan report.

---

## Project Structure

```text
~/the-origin-ai/
├── config/
│   ├── settings.json          # Tracked safe defaults and worker configuration
│   └── settings.local.json    # Gitignored Telegram/Gemini secrets
├── core/
│   ├── ai_brain.py            # Gemini planner, security reviewer, verifier, backoff
│   ├── audit_log.py           # Bounded append-only audit records
│   ├── executor.py            # Workspace-bound subprocess executor
│   ├── memory.py              # Bounded recent-task memory
│   ├── notifier.py            # Lightweight Telegram long polling
│   ├── policy.py              # Deterministic allow/review/deny boundary
│   ├── self_corrector.py      # Gemini correction loop with policy re-checks
│   ├── task_agent.py          # Task IDs, approval, role pipeline, results
│   └── verifier.py            # Read-only verification evidence runner
├── data/                      # Runtime state; ignored by Git
├── main.py                    # Ubuntu worker and Telegram relay entrypoint
├── start_worker.sh            # Portable Ubuntu/Termux worker launcher
├── start_giga.sh              # Compatibility launcher with Termux wake lock
├── setup_ubuntu.sh            # Ubuntu bootstrap and test runner
├── setup_termux.sh            # Lightweight Termux bootstrap
├── requirements.txt           # Requests-only dependency set
└── README.md                  # Project documentation
```

---

## Getting Started

For heavy use, install the bot on an always-on Ubuntu machine. The Redmi 10a only needs the Telegram app; it does not need to run a local LLM or perform the heavy work.

```bash
git clone https://github.com/mega674p-sudo/the-origin-ai.git
cd the-origin-ai
bash setup_ubuntu.sh
```

The setup script asks for the Gemini API key and Telegram bot token, discovers the authorized Telegram user after `/start`, writes secrets to the Gitignored `config/settings.local.json`, runs the full unit suite, and starts the worker. From Telegram, use `/task <goal>`, inspect the returned plan, and execute only with `/approve <task-id>`. Use `/explore pwd` or `/explore git status` for safe diagnostics.

Before running heavy tasks, review the workspace configured in `config/settings.local.json` or the tracked `execution.workspace` default. Do not place secrets in `settings.json`, task goals, shell commands, or Git commits.
