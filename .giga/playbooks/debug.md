# Debug playbook

Use this playbook when the operator asks to diagnose a failure.

The planner should first inspect the workspace and relevant logs with read-only commands. It should state the suspected failure boundary, collect the smallest useful reproduction, and add a declared read-only verification command to each step when possible. Any file edit, dependency installation, service restart, or Git mutation must appear as a separate step and remain behind the task approval gate.

The executor must stop after the first failed step unless Gemini provides a bounded correction that passes the local policy. The verifier must report the exact command output used as evidence. The final report must include the likely cause, changed files, tests run, remaining risks, and whether the issue is actually resolved.
