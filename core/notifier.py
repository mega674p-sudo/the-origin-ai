import httpx
import logging
import asyncio

logger = logging.getLogger("GigaNotifier")

class TelegramNotifier:
    """
    Asynchronous Telegram bot interface for real-time command feedback,
    status updates, and error log streaming back to the operator.
    """
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        if not self.token or self.token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            logger.warning("Telegram bot token not configured. Skipping notification.")
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload, timeout=10.0)
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Failed to send Telegram message: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Telegram notification exception: {str(e)}")
                return False

    def send_message_sync(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Synchronous wrapper for sending Telegram messages."""
        try:
            return asyncio.run(self.send_message(text, parse_mode))
        except RuntimeError:
            # Event loop already running fallback
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.send_message(text, parse_mode))
