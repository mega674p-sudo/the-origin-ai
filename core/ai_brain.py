import os
import logging
import requests

logger = logging.getLogger("GigaAIBrain")

class GeminiBrain:
    """
    Hyper-optimized Gemini API wrapper for Redmi 10a.
    Uses stateless HTTP requests to minimize RAM usage.
    """
    def __init__(self, api_key: str = None, model: str = "gemini-3.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def analyze_error(self, command: str, stderr: str) -> str:
        if not self.api_key or "YOUR" in self.api_key:
            return command

        prompt = f"Fix this bash command. Error: {stderr}\nCommand: {command}\nReturn ONLY the fixed command."
        
        try:
            resp = requests.post(
                self.url,
                params={"key": self.api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=15
            )
            if resp.status_code == 200:
                text = resp.json()['candidates'][0]['content']['parts'][0]['text']
                return text.strip().replace("```bash", "").replace("```", "").strip()
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
        
        return command
