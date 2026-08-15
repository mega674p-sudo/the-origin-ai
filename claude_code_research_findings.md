# Claude-Code-Inspired Upgrade: Research Findings

## Source set 1: Safety, memory, and specialist delegation

Official Claude Code documentation describes a **tool-control layer separate from model instructions**. Its permission rules can allow, ask, or deny particular tool calls, and deny rules override narrower allow rules. The documentation explicitly distinguishes these enforced rules from instructions, which only influence model behavior.[1]

The hook lifecycle provides a useful design pattern for GIGA PHONE AI: session lifecycle hooks, per-turn hooks, and pre/post tool-call hooks. In particular, a pre-tool hook can inspect a proposed shell action and return a deny decision before execution. The documentation warns that best-effort matcher filters are not a hard enforcement boundary; a dedicated permission layer should provide the final deny decision.[2]

Claude Code’s memory model separates concise project instructions from automatically accumulated local notes. The documentation recommends concise, structured project guidance and treats it as context rather than enforcement. It also describes keeping startup memory bounded and moving detail into on-demand topic files.[3]

For delegation, the official documentation describes specialist subagents with separate context, restricted tool sets, focused prompts, and model/cost controls. Its read-only exploration role is especially relevant to GIGA PHONE AI: research and code inspection should be isolated from execution and modification actions.[4]

## Design implications for GIGA PHONE AI

| Claude Code pattern | Adaptation suitable for Gemini + Telegram + Redmi 10a |
|---|---|
| Tool permission layer | Implement local policy evaluation before any command runs; do not rely on Gemini text instructions alone. |
| Pre/post tool lifecycle | Emit structured `before_tool`, `after_tool`, and `tool_failed` events to a lightweight audit log and Telegram. |
| Plan before act | Keep `/task` as planning-only and require `/approve` before any plan executes. |
| Read-only exploration role | Add an `/inspect` or research mode that only reads status/files and cannot invoke a shell command that changes state. |
| Compact project memory | Store a small indexed JSON/Markdown memory with bounded size and topic files; keep secrets out of memory. |
| Specialist delegation | Simulate roles sequentially on the single Gemini API client: planner, security reviewer, executor, verifier. Do not run concurrent model calls on Redmi 10a. |

## References

[1]: https://code.claude.com/docs/en/permissions "Claude Code Docs — Permissions"
[2]: https://code.claude.com/docs/en/hooks "Claude Code Docs — Hooks"
[3]: https://code.claude.com/docs/en/memory "Claude Code Docs — Memory"
[4]: https://code.claude.com/docs/en/sub-agents "Claude Code Docs — Subagents"

## Source set 2: Plan approval, reusable workflows, and context discipline

Claude Code documents plan mode as a workflow in which the agent researches a codebase and presents a plan for approval before making changes. This directly validates the existing GIGA PHONE AI distinction between `/task` and `/approve`, but the implementation should add an explicit verification phase after execution.[5]

The skills documentation distinguishes reusable procedures from always-loaded project instructions. A skill can be invoked directly, and its full body is loaded only when used. The documentation also describes recording reliable run/verify recipes after a clean-environment launch succeeds, so later agent runs use a known procedure instead of rediscovering setup steps.[6]

The extension overview recommends layering always-on project context, on-demand reusable workflows, isolated specialist workers, external connectors, and lifecycle automation instead of placing everything in one prompt. It also warns that every extension consumes context and can add noise.[7]

The context documentation reinforces the low-resource design: large exploration work should be separated and returned as summaries; the main session should keep compact state, clear unrelated tasks, and retain only the essential result of long-running work.[8]

## Additional design implications

| Claude Code pattern | Adaptation suitable for GIGA PHONE AI |
|---|---|
| Plan mode | Keep a persisted task plan, display a numbered risk-aware preview, and require `/approve <task-id>` rather than a global approval. |
| Verification workflow | Add a verifier role that runs only bounded, declared checks after a task completes and reports pass/fail evidence. |
| Skills | Add lightweight project-owned Markdown playbooks for `/debug`, `/review`, `/deploy`, `/n8n`, and `/video` that are loaded only on matching commands. |
| Context compaction | Persist a small task summary after each completed task; retain command/results metadata but truncate raw output. |
| Isolated research | Implement a sequential read-only “explore” pass that can inspect files/status but cannot execute state-changing commands. |

## References added

[5]: https://code.claude.com/docs/en/ultraplan "Claude Code Docs — Plan Mode"
[6]: https://code.claude.com/docs/en/skills "Claude Code Docs — Skills"
[7]: https://code.claude.com/docs/en/features-overview "Claude Code Docs — Features Overview"
[8]: https://code.claude.com/docs/en/context-window "Claude Code Docs — Context Window"

## Source set 3: Core agent loop and practical workflows

Official documentation summarizes the agent loop as **gather context → take action → verify results**. The documented bug-fixing flow explicitly uses test execution, error inspection, source discovery, edits, and another test run. GIGA PHONE AI should therefore treat verification as a first-class state, not simply return success after a command exits zero.[9]

The documented workflow guide emphasizes incremental, testable refactoring; documenting reproduction steps for bugs; using plan-before-editing; preserving clean context through delegated research; and reviewing changes before submission. These patterns are compatible with a Telegram agent when each task has an explicit task record, evidence fields, and a final user-facing summary.[10]

## Additional design implications

| Pattern | Adaptation suitable for GIGA PHONE AI |
|---|---|
| Gather → act → verify | Add task states: `draft`, `awaiting_approval`, `running`, `verifying`, `completed`, `failed`, `cancelled`. |
| Reproduction evidence | Require a task plan to state a verification command or observable completion criterion. |
| Small increments | Enforce one approved plan step at a time and stop on failure; do not continue through a failed plan. |
| Parallel worktrees | Do not emulate concurrent file editing on Redmi 10a; use sequential read-only analysis roles and one writer. |
| Review before submit | Add `/review` to summarize diff, changed files, test evidence, risks, and whether approval is needed for a push. |

## References added

[9]: https://code.claude.com/docs/en/how-claude-code-works "Claude Code Docs — How Claude Code Works"
[10]: https://code.claude.com/docs/en/common-workflows "Claude Code Docs — Common Workflows"
