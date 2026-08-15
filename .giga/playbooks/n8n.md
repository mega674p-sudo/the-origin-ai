# n8n playbook

Use this playbook for n8n installation, configuration, or health checks.

The planner must treat package installation, Docker commands, network downloads, credential configuration, and service restarts as review-sensitive. The plan must never expose credentials in Telegram output or logs. It should create a checkpoint before a change, identify the n8n health endpoint or local service check, and include a read-only verification step after the change.

If n8n is not already installed, the plan must state the exact dependency and storage impact before approval. A successful command alone is not proof of a working service; the verifier must capture a health response or an equivalent process/listener check.
