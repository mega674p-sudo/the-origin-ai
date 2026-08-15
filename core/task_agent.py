import json
import logging
import os
import tempfile
import time
import uuid

from core.policy import ToolPolicy

logger = logging.getLogger("GigaTaskAgent")


class TaskAgent:
    """Approval-gated sequential task runner for the Ubuntu worker."""

    MAX_STEPS = 5
    MAX_COMMAND_LENGTH = 1000
    MAX_RESULT_LENGTH = 1200

    def __init__(self, brain, state_path, policy=None, audit=None, memory=None, verifier=None, checkpoint_dir=None):
        self.brain = brain
        self.state_path = state_path
        self.policy = policy or ToolPolicy()
        self.audit = audit
        self.memory = memory
        self.verifier = verifier
        self.checkpoint_dir = checkpoint_dir

    def _load(self):
        try:
            with open(self.state_path, "r", encoding="utf-8") as state_file:
                state = json.load(state_file)
                return state if isinstance(state, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save(self, state):
        directory = os.path.dirname(self.state_path)
        os.makedirs(directory, exist_ok=True)
        file_descriptor, temporary_path = tempfile.mkstemp(prefix="task_", suffix=".json", dir=directory)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as state_file:
                json.dump(state, state_file, ensure_ascii=False, separators=(",", ":"))
            os.replace(temporary_path, self.state_path)
        except OSError as error:
            logger.error("Unable to save task state: %s", error)
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
            return False
        return True

    def _record(self, event, **details):
        if self.audit:
            self.audit.record(event, **details)

    def _remember(self, state):
        if self.memory:
            self.memory.remember(
                task_id=state.get("task_id", ""),
                goal=state.get("goal", ""),
                status=state.get("status", ""),
                summary=state.get("summary", ""),
                results=state.get("results", []),
            )

    def _validate_plan(self, plan):
        if not isinstance(plan, dict):
            return [], "Gemini did not return a valid plan."
        raw_steps = plan.get("steps")
        if not isinstance(raw_steps, list):
            return [], "Gemini did not return executable steps."

        steps = []
        for raw_step in raw_steps[: self.MAX_STEPS]:
            if not isinstance(raw_step, dict) or raw_step.get("tool") != "run_bash":
                return [], "Plan contains an unsupported tool."
            command = str(raw_step.get("command", "")).strip()
            purpose = str(raw_step.get("purpose", "")).strip()[:240]
            verify = str(raw_step.get("verify", "")).strip()[: self.MAX_COMMAND_LENGTH]
            if not command or len(command) > self.MAX_COMMAND_LENGTH:
                return [], "Plan contains an empty or oversized command."
            decision = self.policy.evaluate(command)
            if decision == "deny":
                self._record("plan_rejected", command=command, reason="local_policy_deny")
                return [], "Plan rejected by the local safety policy."
            if verify and not self.policy.verify_decision(verify):
                return [], "Plan contains a verification command that is not read-only."
            step = {
                "tool": "run_bash",
                "command": command,
                "purpose": purpose,
                "policy": decision,
            }
            if verify:
                step["verify"] = verify
            steps.append(step)
        return steps, ""

    def _requires_checkpoint(self, command: str) -> bool:
        lowered = str(command or "").lower()
        return any(token in lowered for token in ("git push", "git commit", "git reset", "git clean", "git merge", "git rebase"))

    def _has_recent_checkpoint(self, created_at: float) -> bool:
        if not self.checkpoint_dir or not os.path.isdir(self.checkpoint_dir):
            return False
        try:
            return any(
                name.endswith(".json") and os.path.getmtime(os.path.join(self.checkpoint_dir, name)) >= (created_at - 2.0)
                for name in os.listdir(self.checkpoint_dir)
            )
        except OSError:
            return False

    def create_task(self, goal):
        """Ask planner and security-reviewer roles for a plan and persist it for approval."""
        goal = str(goal or "").strip()
        if not goal or len(goal) > 2000:
            return {}, "Task must contain between 1 and 2000 characters."

        plan = self.brain.plan_task(goal)
        steps, validation_error = self._validate_plan(plan)
        if not steps:
            summary = str(plan.get("summary", validation_error))[:500] if plan else validation_error
            return {}, summary

        security = {"status": "unavailable"}
        if hasattr(self.brain, "security_review"):
            security = self.brain.security_review(goal, steps) or security
        if security.get("approved") is False:
            self._record("plan_rejected", reason="security_review", issues=security.get("issues", []))
            return {}, "Plan rejected by the security reviewer. " + "; ".join(security.get("issues", []))[:400]

        task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        state = {
            "task_id": task_id,
            "created_at_epoch": time.time(),
            "status": "awaiting_approval",
            "goal": goal,
            "summary": str(plan.get("summary", "Task plan ready."))[:500],
            "security": security,
            "steps": steps,
            "results": [],
        }
        if not self._save(state):
            return {}, "Unable to save the pending task."
        self._record("task_created", task_id=task_id, goal=goal, steps=len(steps))
        return state, ""

    def get_status(self):
        return self._load()

    def cancel(self, task_id=None):
        state = self._load()
        if state.get("status") != "awaiting_approval":
            return False
        if task_id and task_id != state.get("task_id"):
            return False
        self._record("task_cancelled", task_id=state.get("task_id"))
        try:
            os.unlink(self.state_path)
            return True
        except OSError as error:
            logger.error("Unable to cancel task: %s", error)
            return False

    def approve_and_execute(self, corrector, task_id=None):
        """Execute the pending plan sequentially through policy, corrector, and verifier roles."""
        state = self._load()
        if state.get("status") not in {"awaiting_approval", "checkpoint_required"}:
            return {}, "There is no pending task awaiting approval."
        if not task_id or task_id != state.get("task_id"):
            return {}, "Approval requires the exact task ID shown in the plan."

        state["status"] = "running"
        state["results"] = []
        if not self._save(state):
            return {}, "Unable to mark the task as running."
        self._record("task_approved", task_id=state.get("task_id"))

        for index, step in enumerate(state["steps"], start=1):
            command = step["command"]
            decision = self.policy.evaluate(command)
            if self._requires_checkpoint(command) and not self._has_recent_checkpoint(state.get("created_at_epoch", time.time())):
                state["status"] = "checkpoint_required"
                self._save(state)
                self._remember(state)
                self._record("checkpoint_required", task_id=state.get("task_id"), command=command)
                return state, "Task paused: create /checkpoint <label> after reviewing this plan, then approve again."
            if decision == "deny":
                state["status"] = "blocked_by_policy"
                self._save(state)
                self._remember(state)
                self._record("step_blocked", task_id=state.get("task_id"), command=command)
                return state, "Task stopped by the local safety policy."

            success, stdout, stderr = corrector.execute(command)
            output = stdout if success else stderr
            output = (output or "(no output)")[: self.MAX_RESULT_LENGTH]
            result = {
                "step": index,
                "command": command,
                "success": success,
                "output": output,
                "policy": decision,
            }
            if decision == "review":
                result["warning"] = "Command matched a review-sensitive pattern; execution required this explicit task approval."

            if success and self.verifier and step.get("verify"):
                verification = self.verifier.run(step["verify"])
                result["verification"] = verification
                if not verification.get("verified"):
                    state["results"].append(result)
                    state["status"] = "verification_failed"
                    self._save(state)
                    self._remember(state)
                    return state, "Task stopped because declared verification failed."
            elif success and hasattr(self.brain, "verify_result"):
                ai_verification = self.brain.verify_result(state.get("goal", ""), command, stdout, stderr)
                if ai_verification and ai_verification.get("status") != "unavailable":
                    result["ai_verification"] = ai_verification
                    if ai_verification.get("verified") is False:
                        state["results"].append(result)
                        state["status"] = "verification_failed"
                        self._save(state)
                        self._remember(state)
                        return state, "Task stopped because Gemini could not verify the result."

            state["results"].append(result)
            self._record(
                "step_completed" if success else "step_failed",
                task_id=state.get("task_id"),
                step=index,
                command=command,
                policy=decision,
                output=output,
            )
            if not success:
                state["status"] = "failed"
                self._save(state)
                self._remember(state)
                return state, "Task stopped after the first failed step."

        state["status"] = "completed"
        self._save(state)
        self._remember(state)
        self._record("task_completed", task_id=state.get("task_id"))
        return state, "Task completed with verification evidence."

    @staticmethod
    def format_plan(state):
        lines = [
            f"TASK PLAN [{state.get('task_id', 'unknown')}]",
            str(state.get("summary", "")),
        ]
        security = state.get("security") or {}
        if security.get("risk"):
            lines.append(f"Security review: {security.get('risk')} risk")
        for index, step in enumerate(state.get("steps", []), start=1):
            purpose = f" — {step['purpose']}" if step.get("purpose") else ""
            review = " [REVIEW]" if step.get("policy") == "review" else ""
            lines.append(f"{index}. $ {step['command']}{review}{purpose}")
            if step.get("verify"):
                lines.append(f"   verify: $ {step['verify']}")
        lines.append(f"Reply /approve {state.get('task_id')} to execute, or /cancel to discard.")
        return "\n".join(lines)

    @staticmethod
    def format_result(state, message):
        lines = [f"Task {state.get('task_id', 'unknown')} — {message}"]
        for result in state.get("results", []):
            label = "SUCCESS" if result.get("success") else "FAILED"
            lines.append(f"\nStep {result.get('step')} {label}")
            lines.append(f"$ {result.get('command')}")
            if result.get("warning"):
                lines.append(f"WARNING: {result['warning']}")
            lines.append(str(result.get("output", "")))
            verification = result.get("verification") or result.get("ai_verification")
            if verification:
                lines.append(
                    f"Verification: {verification.get('status', 'checked')} — "
                    f"{verification.get('reason', verification.get('evidence', ''))}"
                )
        return "\n".join(lines)
