import httpx
import logging

logger = logging.getLogger("GigaNotifier")

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.chat_id = chat_id

    async def send_message(self, text: str, parse_mode: str = "Markdown"):
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload, timeout=10.0)
                if response.status_code != 200:
                    logger.error(f"Failed to send Telegram message: {response.text}")
            except Exception as e:
                logger.error(f"Telegram notification exception: {str(e)}")
