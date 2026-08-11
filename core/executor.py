import subprocess
import logging

logger = logging.getLogger("GigaExecutor")

class CommandExecutor:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def run_command(self, command: str) -> tuple[int, str, str]:
        """Executes a bash command securely and returns (exit_code, stdout, stderr)."""
        logger.info(f"Executing command: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                executable="/bin/bash"
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            logger.error(f"Exception during command execution: {str(e)}")
            return -1, "", str(e)
