import logging
import sys
import json
import os
from core.executor import CommandExecutor
from core.notifier import TelegramNotifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GigaMain")

def load_settings():
    settings_path = os.path.join(os.path.dirname(__file__), 'config', 'settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            return json.load(f)
    return {}

def main():
    logger.info("Initializing GIGA PHONE AI Agent Core Modules...")
    
    # Load configuration
    settings = load_settings()
    tg_settings = settings.get("telegram", {})
    bot_token = tg_settings.get("bot_token", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
    chat_id = tg_settings.get("chat_id", "YOUR_CHAT_ID_HERE")

    # 1. Initialize Executor
    executor = CommandExecutor(timeout=30)
    
    # 2. Test Safe Execution (Fixed method name to .run())
    code, stdout, stderr = executor.run("uname -a && python3 --version")
    logger.info(f"Execution Result - Code: {code}")
    if code == 0:
        logger.info(f"STDOUT:\n{stdout}")
    else:
        logger.error(f"STDERR:\n{stderr}")

    # 3. Initialize Notifier and Send Startup Message
    notifier = TelegramNotifier(token=bot_token, chat_id=chat_id)
    logger.info("Telegram Notifier initialized successfully.")
    
    # Send live initialization test message
    notifier.notify("✅ GIGA PHONE AI Agent core initialized successfully!")
    logger.info("Startup notification sent to Telegram.")
    
    logger.info("GIGA PHONE AI initialization test completed successfully.")

if __name__ == "__main__":
    main()
