import requests
import logging

logger = logging.getLogger("GigaNotifier")

class TelegramNotifier:
    """Minimal Telegram bridge for resource-constrained devices."""
    def __init__(self, token: str, chat_id: str):
        self.url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.chat_id = chat_id

    def notify(self, text: str):
        if not self.chat_id or "YOUR" in self.chat_id: return
        try:
            requests.post(self.url, json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            logger.error(f"Notify Error: {e}")
