import json
import os
import re
import tempfile
from datetime import datetime, timezone


class WorkspaceTools:
    """Read-only workspace review plus bounded checkpoint snapshots."""

    MAX_TEXT = 5000

    def __init__(self, executor, policy, data_dir: str, task_state_path: str, memory_path: str):
        self.executor = executor
        self.policy = policy
        self.data_dir = data_dir
        self.task_state_path = task_state_path
        self.memory_path = memory_path
        self.checkpoint_dir = os.path.join(data_dir, "checkpoints")

    def _read_only(self, command: str):
        if not self.policy.verify_decision(command):
            return {"command": command, "status": "rejected", "output": "Policy rejected review command."}
        code, stdout, stderr = self.executor.run(command)
        return {
            "command": command,
            "status": "passed" if code == 0 else "failed",
            "output": (stdout or stderr or "(no output)")[: self.MAX_TEXT],
        }

    def review(self) -> dict:
        checks = [
            self._read_only("git status --short"),
            self._read_only("git diff --stat"),
            self._read_only("git diff --check"),
            self._read_only("git log -1 --oneline"),
        ]
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workspace": self.executor.workspace,
            "checks": checks,
            "risk": "attention_required" if any(item["status"] == "failed" for item in checks) else "reviewed",
        }

    @staticmethod
    def format_review(report: dict) -> str:
        lines = [f"WORKSPACE REVIEW — {report.get('risk', 'unknown')}", f"Workspace: {report.get('workspace', '')}"]
        for check in report.get("checks", []):
            lines.append(f"\n{check.get('command')} [{check.get('status')}]\n{check.get('output', '')}")
        lines.append("\nReview evidence is informational; use /checkpoint <label> before risky operations.")
        return "\n".join(lines)

    def checkpoint(self, label: str = "manual") -> dict:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_label = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(label or "manual"))[:40] or "manual"
        path = os.path.join(self.checkpoint_dir, f"{timestamp}_{safe_label}.json")
        snapshot = {
            "timestamp": timestamp,
            "label": safe_label,
            "workspace": self.executor.workspace,
            "review": self.review(),
            "pending_task": self._load_json(self.task_state_path),
            "recent_memory": self._load_json(self.memory_path),
        }
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        fd, temporary_path = tempfile.mkstemp(prefix="checkpoint_", suffix=".json", dir=self.checkpoint_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as checkpoint_file:
                json.dump(snapshot, checkpoint_file, ensure_ascii=False, indent=2)
                checkpoint_file.write("\n")
            os.replace(temporary_path, path)
        except OSError:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
            return {"ok": False, "error": "Unable to write checkpoint."}
        return {"ok": True, "path": path, "snapshot": snapshot}

    @staticmethod
    def _load_json(path: str):
        try:
            with open(path, "r", encoding="utf-8") as input_file:
                value = json.load(input_file)
            return value
        except (OSError, json.JSONDecodeError):
            return None
