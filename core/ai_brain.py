import json
import logging
import os
import time

import requests

logger = logging.getLogger("GigaAIBrain")


class GeminiBrain:
    """Stateless Gemini API wrapper optimized for low-memory mobile devices."""

    def __init__(self, api_key: str = None, model: str = "gemini-3.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate(self, prompt: str) -> str:
        """Return Gemini text with bounded retry behavior, or an empty string."""
        if not self.api_key or "YOUR_" in self.api_key:
            logger.error("Gemini API key is not configured.")
            return ""

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        # Three total attempts with 1s then 2s bounded backoff on transient API failures.
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
                return ""

        return ""

    def analyze_error(self, command: str, stderr: str) -> str:
        """Return Gemini's corrected command, or the original command on failure."""
        prompt = (
            "Fix this bash command for Termux/Ubuntu. Return ONLY one corrected raw "
            "bash command, with no Markdown or explanation.\n"
            f"Error: {stderr}\nCommand: {command}"
        )
        fixed_command = self.generate(prompt)
        return fixed_command.replace("```bash", "").replace("```", "").strip() or command

    def plan_task(self, goal: str) -> dict:
        """Request a short, strict JSON plan for tools available on the device."""
        prompt = f"""You are the planning component of GIGA PHONE AI on a low-resource Termux device.
Create a safe, concise plan for this user goal: {goal}

Return ONLY valid JSON with this exact structure:
{{"summary":"short summary","steps":[{{"tool":"run_bash","command":"command","purpose":"reason"}}]}}

Rules:
- Use only the tool name "run_bash".
- Include 1 to 5 steps, each command no more than 1000 characters.
- Prefer read-only diagnostics and actions in the current user workspace.
- Never propose sudo, su, rm -rf, mkfs, dd, reboot, shutdown, poweroff, fork bombs, curl/wget piped to a shell, credential access, or destructive commands.
- If the goal would require a forbidden action, return an empty steps array and explain why in summary.
"""
        raw_plan = self.generate(prompt)
        if not raw_plan:
            return {}

        try:
            return json.loads(raw_plan.replace("```json", "").replace("```", "").strip())
        except json.JSONDecodeError:
            logger.error("Gemini returned a non-JSON task plan.")
            return {}
