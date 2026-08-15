# Deploy playbook

Use this playbook for deployment or service changes on the Ubuntu worker.

The planner must identify the target workspace, required dependencies, service lifecycle, health check, rollback point, and expected Telegram report. Before any package installation, permission change, service restart, or Git push, create a checkpoint and show the operation in the approval plan. Never combine a risky mutation with an opaque download-and-execute command.

The verifier must run a read-only health check after the change. A deployment is not complete if the health check, test evidence, or rollback reference is missing.
