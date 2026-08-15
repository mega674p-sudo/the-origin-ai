import json
import logging
import os
import sys
import time

from core.ai_brain import GeminiBrain
from core.audit_log import AuditLog
from core.executor import CommandExecutor
from core.memory import CompactMemory
from core.notifier import TelegramNotifier
from core.playbooks import PlaybookStore
from core.policy import ToolPolicy
from core.self_corrector import SelfCorrector
from core.task_agent import TaskAgent
from core.verifier import CommandVerifier
from core.workspace_tools import WorkspaceTools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("GigaMain")

HELP_TEXT = (
    "GIGA PHONE AI Hybrid Ubuntu Worker commands:\n"
    "/run <bash command> — run a low-risk command immediately\n"
    "/task <goal> — Gemini planner + security review; no command runs yet\n"
    "/approve <task-id> — execute the exact approved plan\n"
    "/cancel <task-id> — discard the pending plan\n"
    "/explore <read-only command> — inspect safely without modifying files\n"
    "/review — show Git/workspace evidence without changing files\n"
    "/checkpoint [label] — snapshot state before risky work\n"
    "/debug, /deploy, /n8n, /video, /review <request> — use a trusted playbook\n"
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
    if text.startswith("/approve"):
        parts = text.split(maxsplit=1)
        return "approve", parts[1].strip() if len(parts) == 2 else ""
    if text.startswith("/cancel"):
        parts = text.split(maxsplit=1)
        return "cancel", parts[1].strip() if len(parts) == 2 else ""
    if text == "/status":
        return "status", ""
    if text == "/review":
        return "review", ""
    if text.startswith("/checkpoint"):
        parts = text.split(maxsplit=1)
        return "checkpoint", parts[1].strip() if len(parts) == 2 else "manual"
    for playbook in ("debug", "review", "deploy", "n8n", "video"):
        prefix = f"/{playbook} "
        if text.startswith(prefix):
            return "playbook", f"{playbook}|{text[len(prefix):].strip()}"
    if text.startswith("/explore ") or text.startswith("/inspect "):
        return "explore", text.split(" ", 1)[1].strip()
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
    logger.info("Initializing GIGA PHONE AI Hybrid Ubuntu Worker...")
    settings = load_settings()
    telegram = settings.get("telegram", {})
    gemini = settings.get("gemini", {})
    execution = settings.get("execution", {})
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")

    bot_token = telegram.get("bot_token", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
    chat_id = telegram.get("chat_id", "YOUR_TELEGRAM_CHAT_ID_HERE")
    allowed_user_id = str(telegram.get("allowed_user_id", "YOUR_ALLOWED_USER_ID_HERE"))

    if "YOUR_" in allowed_user_id:
        logger.error("Telegram allowed_user_id is not configured; listener will not start.")
        return

    policy = ToolPolicy()
    configured_workspace = str(execution.get("workspace", "."))
    workspace = configured_workspace if os.path.isabs(configured_workspace) else os.path.join(base_dir, configured_workspace)
    executor = CommandExecutor(
        timeout=int(execution.get("timeout", 30)),
        max_retries=int(execution.get("max_retries", 3)),
        workspace=workspace,
        max_output=int(execution.get("max_output", 8000)),
    )
    brain = GeminiBrain(api_key=gemini.get("api_key"), model=gemini.get("model", "gemini-3.5-flash"))
    corrector = SelfCorrector(executor, brain=brain, policy=policy)
    notifier = TelegramNotifier(token=bot_token, chat_id=chat_id)
    audit = AuditLog(os.path.join(data_dir, "audit.jsonl"))
    memory = CompactMemory(os.path.join(data_dir, "memory.json"))
    verifier = CommandVerifier(executor, policy)
    task_state_path = os.path.join(data_dir, "pending_task.json")
    task_agent = TaskAgent(
        brain,
        task_state_path,
        policy=policy,
        audit=audit,
        memory=memory,
        verifier=verifier,
        checkpoint_dir=os.path.join(data_dir, "checkpoints"),
    )
    workspace_tools = WorkspaceTools(
        executor,
        policy,
        data_dir,
        task_state_path,
        os.path.join(data_dir, "memory.json"),
    )
    playbooks = PlaybookStore(os.path.join(base_dir, ".giga", "playbooks"))

    if not notifier.enabled:
        logger.error("Telegram bot_token or chat_id is not configured; listener will not start.")
        return

    notifier.notify("GIGA PHONE AI Hybrid Ubuntu Worker is online. Send /help for commands.")
    audit.record("worker_started", allowed_user_id=allowed_user_id)
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
                        audit.record("unauthorized_command", user_id=user_id)
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
                        notifier.notify(
                            f"Task {state.get('task_id', 'unknown')} status: {state.get('status', 'unknown')}\n"
                            f"Goal: {state.get('goal', '')}"
                        )
                    continue
                if action == "review":
                    report = workspace_tools.review()
                    audit.record("workspace_review", risk=report.get("risk"))
                    notifier.notify(WorkspaceTools.format_review(report))
                    continue
                if action == "checkpoint":
                    snapshot = workspace_tools.checkpoint(value or "manual")
                    if snapshot.get("ok"):
                        audit.record("checkpoint_created", path=snapshot.get("path"), label=value or "manual")
                        notifier.notify(f"Checkpoint created: {snapshot.get('path')}")
                    else:
                        notifier.notify(snapshot.get("error", "Checkpoint failed."))
                    continue
                if action == "playbook":
                    playbook_name, request = value.split("|", 1) if "|" in value else ("", "")
                    goal = playbooks.build_goal(playbook_name, request)
                    if not goal:
                        notifier.notify("Playbook request is invalid or unavailable.")
                    else:
                        state, error = task_agent.create_task(goal)
                        notifier.notify(TaskAgent.format_plan(state) if state else f"Task plan not created: {error}")
                    continue
                if action == "cancel":
                    if not value:
                        notifier.notify("Usage: /cancel <task-id>")
                    else:
                        notifier.notify(
                            "Pending task cancelled."
                            if task_agent.cancel(value)
                            else "Task ID does not match the pending task."
                        )
                    continue
                if action == "task":
                    state, error = task_agent.create_task(value)
                    notifier.notify(TaskAgent.format_plan(state) if state else f"Task plan not created: {error}")
                    continue
                if action == "approve":
                    if not value:
                        notifier.notify("Usage: /approve <task-id>")
                        continue
                    notifier.notify("Approved task is running on the Ubuntu worker; this may take several minutes.")
                    state, message_text = task_agent.approve_and_execute(corrector, value)
                    notifier.notify(TaskAgent.format_result(state, message_text) if state else message_text)
                    continue
                if action == "explore":
                    if not value:
                        notifier.notify("Usage: /explore <read-only command>")
                        continue
                    if not policy.verify_decision(value):
                        notifier.notify("Explore rejected: only local read-only commands are allowed.")
                        continue
                    code, stdout, stderr = executor.run(value)
                    audit.record("explore", command=value, success=code == 0, output=stdout or stderr)
                    notifier.notify(
                        f"EXPLORE {'SUCCESS' if code == 0 else 'FAILED'}\n$ {value}\n\n"
                        f"{stdout or stderr or '(no output)'}"
                    )
                    continue

                command = value
                if not command:
                    notifier.notify("Usage: /run <bash command>")
                    continue
                if len(command) > 1000:
                    notifier.notify("Command rejected: maximum command length is 1000 characters.")
                    continue
                decision = policy.evaluate(command)
                if decision == "deny":
                    audit.record("direct_command_blocked", command=command)
                    notifier.notify("Command rejected by the local safety policy.")
                    continue
                if decision == "review":
                    notifier.notify("This command requires a task plan and explicit approval. Use /task <goal>.")
                    continue

                logger.info("Executing authorized low-risk command through self-correction.")
                success, stdout, stderr = corrector.execute(command)
                audit.record("direct_command", command=command, success=success, output=stdout or stderr)
                send_command_result(notifier, command, success, stdout, stderr)

        except KeyboardInterrupt:
            logger.info("GIGA PHONE AI listener stopped by user.")
            break
        except Exception as error:
            logger.exception("Unexpected listener error: %s", error)
            time.sleep(2)


if __name__ == "__main__":
    main()
