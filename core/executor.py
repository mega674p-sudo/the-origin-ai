import subprocess
import logging
import os

logger = logging.getLogger("GigaExecutor")

class CommandExecutor:
    """Minimal subprocess wrapper with strict resource controls."""
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.shell = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"

    def run(self, cmd: str) -> tuple[int, str, str]:
        try:
            res = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, 
                executable=self.shell, timeout=self.timeout
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -1, "", str(e)
