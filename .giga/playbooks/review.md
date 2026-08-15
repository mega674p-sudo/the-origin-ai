# Review playbook

Use this playbook when the operator asks for a change review before commit or deployment.

The planner should gather `git status --short`, `git diff --stat`, and `git diff --check`, then inspect the relevant changed files. It must distinguish implemented evidence from assumptions. The final report should name changed files, tests actually executed, policy-sensitive commands, possible regressions, and a clear recommendation: safe to proceed, needs operator review, or blocked.

Do not commit or push as part of a review unless the operator creates a separate approved task for that operation.
