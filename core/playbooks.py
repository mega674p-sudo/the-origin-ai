import os


class PlaybookStore:
    """Load only repository-local playbooks by allowlisted name."""

    ALLOWED = {"debug", "review", "deploy", "n8n", "video"}

    def __init__(self, directory: str):
        self.directory = directory

    def build_goal(self, name: str, request: str) -> str:
        name = str(name or "").strip().lower()
        request = str(request or "").strip()
        if name not in self.ALLOWED:
            return ""
        if not request or len(request) > 1800:
            return ""
        path = os.path.join(self.directory, f"{name}.md")
        try:
            with open(path, "r", encoding="utf-8") as playbook_file:
                guidance = playbook_file.read()[:5000]
        except OSError:
            return ""
        return f"Apply the trusted {name} playbook below.\n\n{guidance}\n\nOperator request:\n{request}"
