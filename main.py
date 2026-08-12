import json
import logging
import os
import sys
import time

from core.executor import CommandExecutor
from core.notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("GigaMain")


def load_settings():
    settings_path = os.path.join(os.path.dirname(__file__), "config", "settings.json")
    try:
        with open(settings_path, "r", encoding="utf-8") as settings_file:
            return json.load(settings_file)
    except (OSError, json.JSONDecodeError) as error:
        logger.error("Unable to load settings.json: %s", error)
        return {}


def command_from_text(text: str):
    """Accept `/run <bash command>` or a non-empty raw command from the owner."""
    text = (text or "").strip()
    if not text:
        return None
    if text in {"/start", "/help"}:
        return "__HELP__"
    if text.startswith("/run "):
        return text[5:].strip() or None
    return text


def main():
    logger.info("Initializing GIGA PHONE AI Agent Core Modules...")
    settings = load_settings()
    telegram = settings.get("telegram", {})
    execution = settings.get("execution", {})

    bot_token = telegram.get("bot_token", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
    chat_id = telegram.get("chat_id", "YOUR_TELEGRAM_CHAT_ID_HERE")
    allowed_user_id = str(telegram.get("allowed_user_id", "YOUR_ALLOWED_USER_ID_HERE"))

    if "YOUR_" in allowed_user_id:
        logger.error("Telegram allowed_user_id is not configured; listener will not start.")
        return

    executor = CommandExecutor(
        timeout=int(execution.get("timeout", 30)),
        max_retries=int(execution.get("max_retries", 3)),
    )
    notifier = TelegramNotifier(token=bot_token, chat_id=chat_id)

    if not notifier.enabled:
        logger.error("Telegram bot_token or chat_id is not configured; listener will not start.")
        return

    notifier.notify("GIGA PHONE AI listener is online. Send /run <bash command>.")
    logger.info("Telegram long-polling listener started for authorized user %s.", allowed_user_id)

    offset = None
    while True:
        try:
            updates = notifier.get_updates(offset=offset, timeout=30)
            if updates is None:
                time.sleep(2)
                continue

            for update in updates:
                update_id = update.get("update_id")
                if isinstance(update_id, int):
                    offset = update_id + 1

                message = update.get("message") or {}
                sender = message.get("from") or {}
                user_id = sender.get("id")
                text = message.get("text")

                if str(user_id) != allowed_user_id:
                    if user_id is not None:
                        logger.warning("Ignored command from unauthorized Telegram user %s.", user_id)
                    continue

                command = command_from_text(text)
                if command is None:
                    continue
                if command == "__HELP__":
                    notifier.notify("Usage: /run <bash command>")
                    continue

                if len(command) > 1000:
                    notifier.notify("Command rejected: maximum command length is 1000 characters.")
                    continue

                logger.info("Executing authorized Telegram command.")
                code, stdout, stderr = executor.run(command)
                result = stdout if code == 0 else stderr
                if not result:
                    result = "(command completed with no output)" if code == 0 else "(command failed with no error output)"

                status = "SUCCESS" if code == 0 else f"FAILED (exit code {code})"
                notifier.notify(f"{status}\n$ {command}\n\n{result}")

        except KeyboardInterrupt:
            logger.info("GIGA PHONE AI listener stopped by user.")
            break
        except Exception as error:
            logger.exception("Unexpected listener error: %s", error)
            time.sleep(2)


if __name__ == "__main__":
    main()
