import json
import os
import re
import tempfile
from datetime import datetime, timezone


class AuditLog:
    """Append-only JSONL audit trail with bounded storage and secret redaction."""

    MAX_BYTES = 512 * 1024
    MAX_VALUE = 1200
    SECRET_PATTERNS = (
        re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
        re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{20,}\b"),
        re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    )

    def __init__(self, path: str):
        self.path = path

    @classmethod
    def redact(cls, value) -> str:
        text = str(value or "")[: cls.MAX_VALUE]
        for pattern in cls.SECRET_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text

    def record(self, event: str, **details) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": self.redact(event),
            "details": {key: self.redact(value) for key, value in details.items()},
        }
        directory = os.path.dirname(self.path)
        os.makedirs(directory, exist_ok=True)
        try:
            with open(self.path, "a", encoding="utf-8") as audit_file:
                audit_file.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
            self._bound_size()
        except OSError:
            return

    def _bound_size(self) -> None:
        try:
            if os.path.getsize(self.path) <= self.MAX_BYTES:
                return
            with open(self.path, "rb") as audit_file:
                data = audit_file.read()
            kept = data[-self.MAX_BYTES :]
            newline = kept.find(b"\n")
            if newline >= 0:
                kept = kept[newline + 1 :]
            fd, temporary_path = tempfile.mkstemp(prefix="audit_", dir=os.path.dirname(self.path))
            with os.fdopen(fd, "wb") as temporary_file:
                temporary_file.write(kept)
            os.replace(temporary_path, self.path)
        except OSError:
            return
