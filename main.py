import json
import logging
import os
import sys
import time

from core.ai_brain import GeminiBrain
from core.executor import CommandExecutor
from core.notifier import TelegramNotifier
from core.self_corrector import SelfCorrector
from core.task_agent import TaskAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("GigaMain")

HELP_TEXT = (
    "GIGA PHONE AI commands:\n"
    "/run <bash command> — run one command immediately\n"
    "/task <goal> — ask Gemini for a plan; no command runs yet\n"
    "/approve — execute the pending approved plan\n"
    "/cancel — discard the pending plan\n"
    "/status — show task status\n"
    "/help — show this message"
)


def load_settings():
    """Load the tracked template and merge optional local secrets safely."""
    config_dir = os.path.join(os.path.dirname(__file__), "config")
    settings_path = os.path.join(config_dir, "settings.json")
    local_settings_path = os.path.join(config_dir, "settings.local.json")

    try:
        with open(settings_path, "r", encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
    except (OSError, json.JSONDecodeError) as error:
        logger.error("Unable to load settings.json: %s", error)
        return {}

    try:
        with open(local_settings_path, "r", encoding="utf-8") as local_file:
            local_settings = json.load(local_file)
        for section, values in local_settings.items():
            if isinstance(values, dict) and isinstance(settings.get(section), dict):
                settings[section].update(values)
            else:
                settings[section] = values
    except FileNotFoundError:
        pass
    except (OSError, json.JSONDecodeError) as error:
        logger.error("Unable to load settings.local.json: %s", error)

    return settings


def command_from_text(text: str):
    """Parse only explicit Telegram commands from the authorized operator."""
    text = (text or "").strip()
    if text in {"/start", "/help"}:
        return "help", ""
    if text == "/approve":
        return "approve", ""
    if text == "/cancel":
        return "cancel", ""
    if text == "/status":
        return "status", ""
    if text.startswith("/run "):
        return "run", text[5:].strip()
    if text.startswith("/task "):
        return "task", text[6:].strip()
    return None, ""


def send_command_result(notifier, command, success, stdout, stderr):
    result = stdout if success else stderr
    if not result:
        result = "(command completed with no output)" if success else "(command failed with no error output)"
    status = "SUCCESS" if success else "FAILED AFTER SELF-CORRECTION"
    notifier.notify(f"{status}\n$ {command}\n\n{result}")


def main():
    logger.info("Initializing GIGA PHONE AI Agent Core Modules...")
    settings = load_settings()
    telegram = settings.get("telegram", {})
    gemini = settings.get("gemini", {})
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
    brain = GeminiBrain(api_key=gemini.get("api_key"), model=gemini.get("model", "gemini-3.5-flash"))
    corrector = SelfCorrector(executor, brain=brain)
    notifier = TelegramNotifier(token=bot_token, chat_id=chat_id)
    task_state_path = os.path.join(os.path.dirname(__file__), "data", "pending_task.json")
    task_agent = TaskAgent(brain, task_state_path)

    if not notifier.enabled:
        logger.error("Telegram bot_token or chat_id is not configured; listener will not start.")
        return

    notifier.notify("GIGA PHONE AI tool-calling agent is online. Send /help for commands.")
    logger.info("Telegram listener started for authorized user %s.", allowed_user_id)

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

                action, value = command_from_text(text)
                if action is None:
                    continue
                if action == "help":
                    notifier.notify(HELP_TEXT)
                    continue
                if action == "status":
                    state = task_agent.get_status()
                    if not state:
                        notifier.notify("No pending or recorded task.")
                    else:
                        notifier.notify(f"Task status: {state.get('status', 'unknown')}\nGoal: {state.get('goal', '')}")
                    continue
                if action == "cancel":
                    notifier.notify("Pending task cancelled." if task_agent.cancel() else "No task was available to cancel.")
                    continue
                if action == "task":
                    state, error = task_agent.create_task(value)
                    notifier.notify(TaskAgent.format_plan(state) if state else f"Task plan not created: {error}")
                    continue
                if action == "approve":
                    notifier.notify("Approved task is running; this may take several minutes.")
                    state, message_text = task_agent.approve_and_execute(corrector)
                    notifier.notify(TaskAgent.format_result(state, message_text) if state else message_text)
                    continue

                command = value
                if not command:
                    notifier.notify("Usage: /run <bash command>")
                    continue
                if len(command) > 1000:
                    notifier.notify("Command rejected: maximum command length is 1000 characters.")
                    continue

                logger.info("Executing authorized Telegram command through self-correction.")
                success, stdout, stderr = corrector.execute(command)
                send_command_result(notifier, command, success, stdout, stderr)

        except KeyboardInterrupt:
            logger.info("GIGA PHONE AI listener stopped by user.")
            break
        except Exception as error:
            logger.exception("Unexpected listener error: %s", error)
            time.sleep(2)


if __name__ == "__main__":
    main()
