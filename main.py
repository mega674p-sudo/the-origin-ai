import logging
import sys
from core.executor import CommandExecutor
from core.notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GigaMain")

def main():
    logger.info("Initializing GIGA PHONE AI Agent Core Modules...")
    
    # 1. Initialize Executor
    executor = CommandExecutor(timeout=30)
    
    # 2. Test Safe Execution
    code, stdout, stderr = executor.run_command("uname -a && python3 --version")
    logger.info(f"Execution Result - Code: {code}")
    if code == 0:
        logger.info(f"STDOUT:\n{stdout}")
    else:
        logger.error(f"STDERR:\n{stderr}")

    # 3. Initialize Notifier (Placeholder Token)
    notifier = TelegramNotifier(token="YOUR_TELEGRAM_BOT_TOKEN_HERE", chat_id="YOUR_CHAT_ID")
    logger.info("Telegram Notifier initialized successfully.")
    
    logger.info("GIGA PHONE AI initialization test completed successfully.")

if __name__ == "__main__":
    main()
