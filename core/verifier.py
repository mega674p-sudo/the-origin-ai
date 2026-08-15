class CommandVerifier:
    """Runs declared read-only verification commands and records evidence."""

    MAX_OUTPUT = 1200

    def __init__(self, executor, policy):
        self.executor = executor
        self.policy = policy

    def run(self, command: str) -> dict:
        command = str(command or "").strip()
        if not command:
            return {"status": "not_declared", "verified": True, "evidence": ""}
        if not self.policy.verify_decision(command):
            return {
                "status": "rejected",
                "verified": False,
                "evidence": "Verification command is not a local read-only command.",
            }
        code, stdout, stderr = self.executor.run(command)
        evidence = (stdout if code == 0 else stderr) or "(no verification output)"
        return {
            "status": "passed" if code == 0 else "failed",
            "verified": code == 0,
            "command": command,
            "evidence": evidence[: self.MAX_OUTPUT],
        }
