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

    def analyze_error(self, command: str, stderr: str) -> str:
        """Return Gemini's corrected command, or the original command on failure."""
        if not self.api_key or "YOUR_" in self.api_key:
            return command

        prompt = (
            "Fix this bash command for Termux/Ubuntu. Return ONLY one corrected raw "
            "bash command, with no Markdown or explanation.\n"
            f"Error: {stderr}\nCommand: {command}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        # Three total attempts with 1s then 2s bounded backoff on rate limits.
        for attempt in range(3):
            try:
                response = requests.post(
                    self.url,
                    params={"key": self.api_key},
                    json=payload,
                    timeout=15,
                )

                if response.status_code == 200:
                    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                    fixed_command = text.strip().replace("```bash", "").replace("```", "").strip()
                    return fixed_command or command

                if response.status_code == 429 and attempt < 2:
                    delay = 2 ** attempt
                    logger.warning(
                        "Gemini API rate-limited request; retrying in %s second(s) [%s/3].",
                        delay,
                        attempt + 1,
                    )
                    time.sleep(delay)
                    continue

                logger.error("Gemini API returned HTTP %s.", response.status_code)
                return command

            except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
                logger.error("Gemini API request failed: %s", error)
                return command

        return command
