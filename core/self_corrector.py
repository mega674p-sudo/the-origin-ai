import logging
from core.executor import CommandExecutor

logger = logging.getLogger("GigaSelfCorrector")

class SelfCorrector:
    def __init__(self, executor: CommandExecutor):
        self.executor = executor

    def suggest_fix(self, command: str, stderr: str) -> str:
        """
        Analyzes stderr and applies heuristics or local LLM prompt refinement 
        to fix common Termux/Ubuntu CLI errors (e.g., missing packages, permission denied).
        """
        stderr_lower = stderr.lower()
        
        if "command not found" in stderr_lower:
            pkg = command.split()[0]
            logger.warning(f"Missing dependency detected: {pkg}. Attempting auto-install...")
            return f"pkg install -y {pkg} || apt-get install -y {pkg} && {command}"
        
        if "permission denied" in stderr_lower:
            logger.warning("Permission denied detected. Prepending sudo/su...")
            return f"sudo {command}"
            
        if "no such file or directory" in stderr_lower:
            logger.warning("Path error detected. Inspecting directory structure...")
            return f"mkdir -p $(dirname {command.split()[-1]}) && {command}"

        return command

    def execute_with_correction(self, command: str) -> tuple[bool, str, str]:
        current_cmd = command
        for attempt in range(self.executor.max_retries):
            code, stdout, stderr = self.executor.run_command(current_cmd)
            if code == 0:
                return True, stdout, stderr
            
            logger.error(f"Attempt {attempt + 1} failed for: {current_cmd}. Error: {stderr}")
            current_cmd = self.suggest_fix(current_cmd, stderr)
            
        return False, "", f"Failed after {self.executor.max_retries} attempts."
