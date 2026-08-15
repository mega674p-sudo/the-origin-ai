import json
import os
import tempfile
from datetime import datetime, timezone


class CompactMemory:
    """Small bounded memory index for recent task outcomes."""

    MAX_ENTRIES = 40
    MAX_FIELD = 1200

    def __init__(self, path: str):
        self.path = path

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as memory_file:
                data = json.load(memory_file)
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self, entries):
        directory = os.path.dirname(self.path)
        os.makedirs(directory, exist_ok=True)
        fd, temporary_path = tempfile.mkstemp(prefix="memory_", suffix=".json", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as memory_file:
                json.dump(entries[-self.MAX_ENTRIES :], memory_file, ensure_ascii=False, separators=(",", ":"))
            os.replace(temporary_path, self.path)
        except OSError:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass

    def remember(self, task_id: str, goal: str, status: str, summary: str, results=None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": str(task_id)[:100],
            "goal": str(goal or "")[: self.MAX_FIELD],
            "status": str(status or "")[:80],
            "summary": str(summary or "")[: self.MAX_FIELD],
            "results": results if isinstance(results, list) else [],
        }
        entries = self._load()
        entries.append(entry)
        self._save(entries)

    def recent(self, limit: int = 5):
        return self._load()[-max(1, min(int(limit), 10)) :]

    def context_text(self, limit: int = 5) -> str:
        lines = []
        for entry in self.recent(limit):
            lines.append(
                f"{entry.get('task_id')}: {entry.get('status')} — "
                f"{entry.get('goal', '')[:180]} — {entry.get('summary', '')[:180]}"
            )
        return "\n".join(lines) or "No previous task context."
