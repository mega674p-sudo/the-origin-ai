import os
import json
import logging
import requests

logger = logging.getLogger("GigaAIBrain")

class GeminiBrain:
    """
    Lightweight Gemini API wrapper for low-RAM mobile devices (Redmi 10a).
    Offloads all reasoning and error analysis to Google's Gemini 1.5 Flash API.
    """
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
        self.model = model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def analyze_error(self, command: str, stderr: str) -> str:
        """Sends failed command and error output to Gemini to get a corrected bash command."""
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY_HERE":
            logger.warning("Gemini API key not configured. Returning original command.")
            return command

        prompt = f"""You are an expert Linux/Termux systems engineer. A bash command failed. Provide ONLY the corrected, raw bash command without markdown formatting or explanation.

Failed Command: {command}
Error Output (Stderr): {stderr}

Corrected Bash Command:"""

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            response = requests.post(self.api_url, headers=headers, params=params, json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    cleaned = text.strip().replace("```bash", "").replace("```", "").strip()
                    if cleaned:
                        logger.info(f"Gemini suggested fix: {cleaned}")
                        return cleaned
            else:
                logger.error(f"Gemini API error ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Gemini API exception: {str(e)}")

        return command
