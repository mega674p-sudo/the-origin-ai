import logging

from core.ai_brain import GeminiBrain
from core.executor import CommandExecutor
from core.policy import ToolPolicy

logger = logging.getLogger("GigaSelfCorrector")


class SelfCorrector:
    """Retry failed commands after bounded Gemini correction under local policy control."""

    def __init__(self, executor: CommandExecutor, api_key: str = None, brain: GeminiBrain = None, policy=None):
        self.executor = executor
        self.brain = brain or GeminiBrain(api_key=api_key)
        self.policy = policy or ToolPolicy()

    def execute(self, cmd: str) -> tuple[bool, str, str]:
        current_cmd = str(cmd or "").strip()
        for attempt in range(self.executor.max_retries):
            decision = self.policy.evaluate(current_cmd)
            if decision == "deny":
                return False, "", "Command blocked by the local safety policy."

            code, stdout, stderr = self.executor.run(current_cmd)
            if code == 0:
                return True, stdout, stderr

            logger.warning("Retry %s for a failed command.", attempt + 1)
            corrected_cmd = self.brain.analyze_error(current_cmd, stderr)
            if self.policy.evaluate(corrected_cmd) == "deny":
                return False, "", "Gemini proposed a command blocked by the local safety policy."
            if corrected_cmd == current_cmd:
                break
            current_cmd = corrected_cmd

        return False, "", "Max retries reached or no safe correction was returned."

    def execute_with_correction(self, cmd: str) -> tuple[bool, str, str]:
        """Compatibility alias for legacy callers."""
        return self.execute(cmd)
