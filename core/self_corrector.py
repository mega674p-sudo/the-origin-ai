import logging
from core.executor import CommandExecutor
from core.ai_brain import GeminiBrain

logger = logging.getLogger("GigaSelfCorrector")

class SelfCorrector:
    def __init__(self, executor: CommandExecutor, api_key: str = None):
        self.executor = executor
        self.brain = GeminiBrain(api_key=api_key)

    def execute(self, cmd: str) -> tuple[bool, str, str]:
        current_cmd = cmd
        for i in range(self.executor.max_retries):
            code, out, err = self.executor.run(current_cmd)
            if code == 0:
                return True, out, err
            
            logger.warning(f"Retry {i+1} for: {current_cmd}")
            current_cmd = self.brain.analyze_error(current_cmd, err)
            
        return False, "", "Max retries reached."
