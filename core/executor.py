import subprocess
import logging
import os

logger = logging.getLogger("GigaExecutor")

class CommandExecutor:
    """
    Secure subprocess wrapper optimized for mobile Termux and Ubuntu environments.
    Executes system bash commands, captures stdout/stderr, and handles exit codes.
    """
    def __init__(self, timeout: int = 60, shell_path: str = "/bin/bash", max_retries: int = 3):
        self.timeout = timeout
        self.shell_path = shell_path if os.path.exists(shell_path) else "/bin/sh"
        self.max_retries = max_retries

    def run_command(self, command: str) -> tuple[int, str, str]:
        """
        Executes a bash command securely and returns a tuple of (exit_code, stdout, stderr).
        """
        logger.info(f"Executing command: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                executable=self.shell_path,
                timeout=self.timeout
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            error_msg = f"Command execution timed out after {self.timeout} seconds: {command}"
            logger.error(error_msg)
            return -1, "", error_msg
        except Exception as e:
            error_msg = f"Exception during command execution: {str(e)}"
            logger.error(error_msg)
            return -1, "", error_msg
