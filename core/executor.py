import logging
import os
import shutil
import subprocess

logger = logging.getLogger("GigaExecutor")


class CommandExecutor:
    """Minimal subprocess wrapper with strict timeouts and Termux shell support."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = max(1, int(timeout))
        self.max_retries = max(1, int(max_retries))
        self.shell = self._find_shell()

    @staticmethod
    def _find_shell():
        """Prefer the active Termux shell, then portable bash/sh locations."""
        candidates = [
            os.environ.get("SHELL", ""),
            shutil.which("bash") or "",
            shutil.which("sh") or "",
            "/bin/bash",
            "/bin/sh",
        ]
        for candidate in candidates:
            if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return None

    def run(self, cmd: str) -> tuple[int, str, str]:
        if not self.shell:
            return -1, "", "No executable shell was found."
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                executable=self.shell,
                timeout=self.timeout,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except OSError as error:
            logger.error("Command execution failed: %s", error)
            return -1, "", str(error)
