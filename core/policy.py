import re


class ToolPolicy:
    """Small deterministic policy layer that runs before any shell tool."""

    DENY_PATTERNS = (
        "rm -rf",
        "rm -fr",
        "mkfs",
        "dd if=",
        "reboot",
        "shutdown",
        "poweroff",
        ":(){",
        "fork bomb",
        "termux-wipe",
        "curl | sh",
        "curl | bash",
        "wget | sh",
        "wget | bash",
        "curl -fssl",
    )

    REVIEW_PATTERNS = (
        "git push",
        "git commit",
        "git reset",
        "git clean",
        "git checkout",
        "git merge",
        "git rebase",
        "git clone",
        "git apply",
        "rm ",
        "mv ",
        "cp ",
        "touch ",
        "mkdir ",
        "tee ",
        "python ",
        "python3 ",
        "bash ",
        "sh ",
        "sed -i",
        "perl -i",
        "systemctl ",
        "docker ",
        "apt ",
        "apt-get ",
        "pkg ",
        "pip ",
        "npm ",
        "pnpm ",
        "yarn ",
        "curl ",
        "wget ",
        "chmod ",
        "chown ",
    )

    READ_ONLY_PREFIXES = (
        "pwd",
        "ls",
        "cat ",
        "head ",
        "tail ",
        "grep ",
        "rg ",
        "find ",
        "wc ",
        "which ",
        "command -v ",
        "stat ",
        "du ",
        "df ",
        "free ",
        "uname",
        "whoami",
        "id",
        "date",
        "git status",
        "git log ",
        "git diff --check",
        "git diff --stat",
        "python --version",
        "python3 --version",
        "test ",
    )

    def evaluate(self, command: str) -> str:
        """Return one of allow, review, or deny using only local deterministic rules."""
        normalized = re.sub(r"\s+", " ", str(command or "").strip().lower())
        if not normalized or len(normalized) > 1000:
            return "deny"
        if any(pattern in normalized for pattern in self.DENY_PATTERNS):
            return "deny"
        if re.search(r"\b(sudo|su)\b", normalized):
            return "deny"
        if any(pattern in normalized for pattern in self.REVIEW_PATTERNS):
            return "review"
        if re.search(r"(^|[\s;&|])(>>?|[0-9]>>?|tee)(\s|$)", normalized):
            return "review"
        return "allow"

    def is_read_only(self, command: str) -> bool:
        """Allow verification only for simple read-only command chains."""
        parts = re.split(r"\s*(?:&&|;|\|\|)\s*", str(command or "").strip().lower())
        if not parts or any(not part for part in parts):
            return False
        return all(part.startswith(self.READ_ONLY_PREFIXES) for part in parts)

    def verify_decision(self, command: str) -> bool:
        return self.evaluate(command) == "allow" and self.is_read_only(command)
