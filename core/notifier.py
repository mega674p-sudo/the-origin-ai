import logging

import requests

logger = logging.getLogger("GigaNotifier")


class TelegramNotifier:
    """Minimal Telegram API client using blocking long polling and no heavy SDK."""

    def __init__(self, token: str, chat_id: str):
        self.chat_id = str(chat_id or "")
        self.enabled = bool(token and "YOUR_" not in token and self.chat_id and "YOUR_" not in self.chat_id)
        base_url = f"https://api.telegram.org/bot{token}"
        self.send_url = f"{base_url}/sendMessage"
        self.updates_url = f"{base_url}/getUpdates"

    def notify(self, text: str) -> bool:
        """Send a bounded plain-text message to the configured operator chat."""
        if not self.enabled:
            logger.warning("Telegram notifier is not configured; message was not sent.")
            return False

        text = str(text)
        if len(text) > 4000:
            text = f"{text[:3960]}\n...[output truncated]"

        try:
            response = requests.post(
                self.send_url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "disable_web_page_preview": True,
                },
                timeout=10,
            )
            response.raise_for_status()
            return bool(response.json().get("ok"))
        except (requests.RequestException, ValueError) as error:
            logger.error("Telegram sendMessage failed: %s", error)
            return False

    def get_updates(self, offset=None, timeout: int = 30):
        """
        Return pending Telegram updates, or None when a network/API error occurs.

        Telegram holds the request for 25 seconds while the HTTP client uses a
        strict 30-second timeout. This keeps idle CPU usage close to zero while
        still allowing the caller to back off after connection failures.
        """
        if not self.enabled:
            logger.error("Telegram listener is not configured.")
            return None

        request_timeout = max(10, min(int(timeout), 30))
        poll_timeout = max(1, min(request_timeout - 5, 25))
        params = {"timeout": poll_timeout}
        if offset is not None:
            params["offset"] = int(offset)

        try:
            response = requests.get(self.updates_url, params=params, timeout=request_timeout)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                logger.error("Telegram getUpdates returned an unsuccessful response.")
                return None
            updates = payload.get("result", [])
            return updates if isinstance(updates, list) else None
        except (requests.RequestException, ValueError, TypeError) as error:
            logger.warning("Telegram getUpdates failed: %s", error)
            return None
