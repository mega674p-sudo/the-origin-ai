import json
import logging
import os
import time

import requests

logger = logging.getLogger("GigaAIBrain")


class GeminiBrain:
    """Stateless Gemini API wrapper with bounded specialist-role calls."""

    def __init__(self, api_key: str = None, model: str = "gemini-3.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate(self, prompt: str) -> str:
        """Return Gemini text with three total attempts and bounded exponential backoff."""
        if not self.api_key or "YOUR_" in self.api_key:
            logger.error("Gemini API key is not configured.")
            return ""

        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        for attempt in range(3):
            try:
                response = requests.post(
                    self.url,
                    params={"key": self.api_key},
                    json=payload,
                    timeout=20,
                )
                if response.status_code == 200:
                    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

                if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                    delay = 2 ** attempt
                    logger.warning(
                        "Gemini API transient HTTP %s; retrying in %s second(s) [%s/3].",
                        response.status_code,
                        delay,
                        attempt + 1,
                    )
                    time.sleep(delay)
                    continue

                logger.error("Gemini API returned HTTP %s.", response.status_code)
                return ""
            except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
                logger.error("Gemini API request failed: %s", error)
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                return ""
        return ""

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = (raw or "").replace("```json", "").replace("```", "").strip()
        try:
            value = json.loads(cleaned)
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            logger.error("Gemini returned non-JSON specialist output.")
            return {}

    def analyze_error(self, command: str, stderr: str) -> str:
        prompt = (
            "Fix this bash command for Ubuntu/Termux. Return ONLY one corrected raw bash "
            "command, with no Markdown or explanation. Do not use sudo, destructive commands, "
            "credential access, or download-and-execute patterns.\n"
            f"Error: {stderr}\nCommand: {command}"
        )
        fixed_command = self.generate(prompt)
        return fixed_command.replace("```bash", "").replace("```", "").strip() or command

    def plan_task(self, goal: str) -> dict:
        """Planner role: produce a short executable plan with optional read-only checks."""
        prompt = f"""You are the planner component of GIGA PHONE AI's Ubuntu worker.
Create a safe, concise plan for this user goal: {goal}

Return ONLY valid JSON with this exact structure:
{{"summary":"short summary","steps":[{{"tool":"run_bash","command":"command","purpose":"reason","verify":"optional read-only verification command"}}]}}

Rules:
- Use only the tool name run_bash.
- Include 1 to 5 steps; each command must be no more than 1000 characters.
- Prefer the current workspace and read-only diagnostics.
- The optional verify command must be read-only and suitable for local policy verification.
- Never propose sudo, su, rm -rf, mkfs, dd, reboot, shutdown, poweroff, fork bombs,
  curl/wget piped to a shell, credential access, or destructive commands.
- If the goal requires a forbidden action, return an empty steps array and explain why.
"""
        raw_plan = self.generate(prompt)
        return self._parse_json(raw_plan) if raw_plan else {}

    def security_review(self, goal: str, steps: list) -> dict:
        """Security-reviewer role: assess the plan independently of local policy."""
        prompt = f"""You are the security reviewer for an Ubuntu coding worker.
Review this proposed plan for the goal below.
Goal: {goal}
Plan: {json.dumps(steps, ensure_ascii=False)}

Return ONLY valid JSON:
{{"approved":true,"risk":"low|medium|high","issues":["..."],"required_confirmation":"none|operator"}}

Reject plans containing destructive system operations, privilege escalation, secret access,
download-and-execute behavior, or commands that can affect data outside the project workspace.
"""
        raw = self.generate(prompt)
        return self._parse_json(raw) if raw else {"status": "unavailable"}

    def verify_result(self, goal: str, command: str, stdout: str, stderr: str = "") -> dict:
        """Verifier role: decide whether a successful tool result supports the goal."""
        prompt = f"""You are the verification component of a coding agent.
Determine whether this command result supports completion of the stated goal.
Goal: {goal}
Command: {command}
STDOUT: {stdout[:3000]}
STDERR: {stderr[:1500]}

Return ONLY valid JSON:
{{"verified":true,"confidence":"high|medium|low","reason":"short evidence-based reason"}}
Do not invent evidence. If the output is insufficient, set verified to false.
"""
        raw = self.generate(prompt)
        return self._parse_json(raw) if raw else {"status": "unavailable"}
