import logging
from core.executor import CommandExecutor
from core.ai_brain import GeminiBrain

logger = logging.getLogger("GigaSelfCorrector")

class SelfCorrector:
    """
    Self-correction loop integrated with GeminiBrain for intelligent error fixing
    on resource-constrained mobile devices.
    """
    def __init__(self, executor: CommandExecutor, gemini_api_key: str = None):
        self.executor = executor
        self.brain = GeminiBrain(api_key=gemini_api_key)

    def execute_with_correction(self, command: str) -> tuple[bool, str, str]:
        current_cmd = command
        for attempt in range(self.executor.max_retries):
            code, stdout, stderr = self.executor.run_command(current_cmd)
            if code == 0:
                return True, stdout, stderr
            
            logger.error(f"Attempt {attempt + 1} failed for: {current_cmd}. Error: {stderr}")
            
            # Consult Gemini Brain for intelligent fix
            current_cmd = self.brain.analyze_error(current_cmd, stderr)
            
        return False, "", f"Command failed after {self.executor.max_retries} attempts."
