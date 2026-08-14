import json
import logging
import os
import re
import tempfile

logger = logging.getLogger("GigaTaskAgent")


class TaskAgent:
    """Gemini-planned task runner with one persisted, approval-gated task."""

    MAX_STEPS = 5
    MAX_COMMAND_LENGTH = 1000
    MAX_RESULT_LENGTH = 1200
    FORBIDDEN_PATTERNS = (
        "rm -rf",
        "mkfs",
        "dd if=",
        "reboot",
        "shutdown",
        "poweroff",
        ":(){",
        "sudo ",
        "su -",
        "termux-wipe",
    )

    def __init__(self, brain, state_path):
        self.brain = brain
        self.state_path = state_path

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

    def _is_safe_command(self, command):
        lowered = command.lower()
        if not command or len(command) > self.MAX_COMMAND_LENGTH:
            return False
        if any(pattern in lowered for pattern in self.FORBIDDEN_PATTERNS):
            return False
        if re.search(r"\b(curl|wget)\b[^\n]*\|\s*(sh|bash)\b", lowered):
            return False
        return True

    def _validate_plan(self, plan):
        if not isinstance(plan, dict):
            return []
        raw_steps = plan.get("steps")
        if not isinstance(raw_steps, list):
            return []

        steps = []
        for raw_step in raw_steps[: self.MAX_STEPS]:
            if not isinstance(raw_step, dict) or raw_step.get("tool") != "run_bash":
                return []
            command = str(raw_step.get("command", "")).strip()
            purpose = str(raw_step.get("purpose", "")).strip()[:240]
            if not self._is_safe_command(command):
                return []
            steps.append({"tool": "run_bash", "command": command, "purpose": purpose})
        return steps

    def create_task(self, goal):
        """Ask Gemini for a plan and persist it until the owner approves or cancels."""
        goal = str(goal or "").strip()
        if not goal or len(goal) > 2000:
            return {}, "Task must contain between 1 and 2000 characters."

        plan = self.brain.plan_task(goal)
        steps = self._validate_plan(plan)
        if not steps:
            summary = str(plan.get("summary", "Gemini did not return a safe executable plan."))[:500] if plan else "Gemini planning failed."
            return {}, summary

        state = {
            "status": "awaiting_approval",
            "goal": goal,
            "summary": str(plan.get("summary", "Task plan ready."))[:500],
            "steps": steps,
            "results": [],
        }
        if not self._save(state):
            return {}, "Unable to save the pending task."
        return state, ""

    def get_status(self):
        return self._load()

    def cancel(self):
        state = self._load()
        if state.get("status") != "awaiting_approval":
            return False
        try:
            os.unlink(self.state_path)
            return True
        except OSError as error:
            logger.error("Unable to cancel task: %s", error)
            return False

    def approve_and_execute(self, corrector):
        """Execute the pending plan sequentially through the Gemini self-corrector."""
        state = self._load()
        if state.get("status") != "awaiting_approval":
            return {}, "There is no pending task awaiting approval."

        state["status"] = "running"
        state["results"] = []
        if not self._save(state):
            return {}, "Unable to mark the task as running."

        for index, step in enumerate(state["steps"], start=1):
            command = step["command"]
            success, stdout, stderr = corrector.execute(command)
            output = stdout if success else stderr
            output = (output or "(no output)")[: self.MAX_RESULT_LENGTH]
            result = {
                "step": index,
                "command": command,
                "success": success,
                "output": output,
            }
            state["results"].append(result)
            if not success:
                state["status"] = "failed"
                self._save(state)
                return state, "Task stopped after the first failed step."

        state["status"] = "completed"
        self._save(state)
        return state, "Task completed."

    @staticmethod
    def format_plan(state):
        lines = [f"TASK PLAN\n{state.get('summary', '')}"]
        for index, step in enumerate(state.get("steps", []), start=1):
            purpose = f" — {step['purpose']}" if step.get("purpose") else ""
            lines.append(f"{index}. $ {step['command']}{purpose}")
        lines.append("Reply /approve to execute, or /cancel to discard.")
        return "\n".join(lines)

    @staticmethod
    def format_result(state, message):
        lines = [message]
        for result in state.get("results", []):
            label = "SUCCESS" if result.get("success") else "FAILED"
            lines.append(f"\nStep {result.get('step')} {label}\n$ {result.get('command')}\n{result.get('output')}")
        return "\n".join(lines)
