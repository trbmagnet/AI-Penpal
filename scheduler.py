import signal
import threading
import time
import uuid
from datetime import datetime

from ai_client import AIClient, create_client
from config import AppConfig
from email_client import IMAPClient, SMTPSender
from email_parser import parse_email
from logger import setup_logger
from tracker import ReplyTracker

logger = setup_logger()


def build_system_prompt(character_config) -> str:
    parts = [f"你是{character_config.name}。"]
    if character_config.personality:
        parts.append(f"性格特点：{character_config.personality}")
    if character_config.background:
        parts.append(f"背景设定：{character_config.background}")
    if character_config.writing_style:
        parts.append(f"写作风格：{character_config.writing_style}")
    parts.append("")
    parts.append("你正在回复一封邮件。请以你的角色身份进行回复。")
    parts.append("不要包含邮件主题行，只写邮件正文内容。")
    return "\n".join(parts)


def build_email_message(parsed_email) -> str:
    parts = []
    parts.append(f"发件人：{parsed_email.sender}")
    if parsed_email.subject:
        parts.append(f"主题：{parsed_email.subject}")
    if parsed_email.date:
        parts.append(f"日期：{parsed_email.date.strftime('%Y-%m-%d %H:%M')}")
    parts.append("")
    parts.append("邮件内容：")
    parts.append(parsed_email.body or "(无正文)")
    if parsed_email.attachments:
        parts.append("")
        parts.append("附件：")
        for att in parsed_email.attachments:
            parts.append(f"  - {att.filename} ({att.content_type}, {att.size} bytes)")
    return "\n".join(parts)


def build_history_context(tracker, sender: str, current_email_message: str,
                          history_config) -> tuple[str, list[dict]]:
    if not history_config.enabled:
        return current_email_message, []

    summary = tracker.get_summary(sender)
    recent_messages = tracker.get_history(sender, limit=history_config.max_recent_messages)

    history = []
    for msg in recent_messages:
        history.append({"role": msg["role"], "content": msg["content"]})

    message_with_summary = current_email_message
    if summary:
        message_with_summary = (
            f"[之前的对话摘要]\n{summary['summary_text']}\n\n"
            f"{current_email_message}"
        )

    return message_with_summary, history


def maybe_summarize(tracker, ai_client, sender: str, history_config):
    if not history_config.enabled:
        return

    count = tracker.get_exchange_count(sender)
    if count == 0 or count % history_config.summarize_every_n != 0:
        return

    old_messages = tracker.get_old_messages_for_sender(
        sender, exclude_recent=history_config.max_recent_messages
    )
    if not old_messages:
        return

    logger.info("Summarizing %d old messages for %s", len(old_messages), sender)
    summary_text = ai_client.summarize_history(old_messages)
    tracker.update_summary(sender, summary_text, count - len(old_messages))
    logger.info("Summary updated for %s (%d chars)", sender, len(summary_text))


def check_and_reply(config: AppConfig, ai_client: AIClient, tracker: ReplyTracker):
    imap_client = IMAPClient(config.email)
    smtp_sender = SMTPSender(config.email)

    try:
        imap_client.connect()
        raw_emails = imap_client.fetch_recent_emails(
            config.filters.ignore_older_than_minutes
        )

        for msg_id, raw_msg in raw_emails:
            parsed_email = parse_email(raw_msg)

            if not parsed_email.sender:
                logger.warning("Skipping email with no sender")
                continue

            sender_email = parsed_email.sender
            if config.filters.allowed_senders:
                if sender_email not in config.filters.allowed_senders:
                    logger.info("Skipping email from %s (not in allowed_senders)", sender_email)
                    continue

            if not parsed_email.message_id:
                parsed_email.message_id = f"<synthetic-{uuid.uuid4()}@ai_penpal>"
                logger.info("Generated synthetic Message-ID: %s", parsed_email.message_id)

            if tracker.has_replied(parsed_email.message_id):
                logger.info("Already replied to %s, skipping", parsed_email.message_id)
                continue

            logger.info(
                "Processing email from %s: %s",
                parsed_email.sender_name or parsed_email.sender,
                parsed_email.subject or "(no subject)",
            )

            system_prompt = build_system_prompt(config.character)
            email_message = build_email_message(parsed_email)

            message_for_ai, history = build_history_context(
                tracker, parsed_email.sender, email_message, config.history
            )

            try:
                reply_body = ai_client.generate_reply(system_prompt, message_for_ai, history=history)
                logger.info("AI generated reply (%d chars)", len(reply_body))
            except Exception as e:
                logger.error("AI generation failed: %s", e)
                continue

            try:
                smtp_sender.connect()
                smtp_sender.send_reply(parsed_email, reply_body)
                tracker.mark_replied(parsed_email.message_id)
                tracker.store_exchange(
                    sender=parsed_email.sender,
                    role="user",
                    content=parsed_email.body or "",
                    subject=parsed_email.subject,
                    message_id=parsed_email.message_id,
                )
                tracker.store_exchange(
                    sender=parsed_email.sender,
                    role="assistant",
                    content=reply_body,
                    subject=f"Re: {parsed_email.subject}" if parsed_email.subject else "",
                )
                maybe_summarize(tracker, ai_client, parsed_email.sender, config.history)
                logger.info("Successfully replied to %s", parsed_email.sender)
            except Exception as e:
                logger.error("Failed to send reply to %s: %s", parsed_email.sender, e)
            finally:
                smtp_sender.disconnect()

    except Exception as e:
        logger.error("Error during email check: %s", e)
    finally:
        imap_client.disconnect()


def run_scheduler(config: AppConfig, stop_event: threading.Event | None = None):
    tracker = ReplyTracker(config.tracking.db_path)
    tracker.cleanup(config.tracking.cleanup_days)

    ai_client = create_client(
        provider=config.model.provider,
        api_key=config.model.api_key,
        model_name=config.model.model_name,
        base_url=config.model.base_url,
        max_tokens=config.model.max_tokens,
        temperature=config.model.temperature,
    )

    interval_seconds = config.scheduler.check_interval_minutes * 60

    if stop_event is None:
        import signal
        _cli_stop = True

        def signal_handler(sig, frame):
            nonlocal _cli_stop
            logger.info("Received shutdown signal, stopping...")
            _cli_stop = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        is_running = lambda: _cli_stop
    else:
        is_running = lambda: not stop_event.is_set()

    logger.info(
        "AI Pen Pal started. Checking emails every %d minute(s).",
        config.scheduler.check_interval_minutes,
    )

    while is_running():
        logger.info("--- Checking emails at %s ---", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        check_and_reply(config, ai_client, tracker)

        if not is_running():
            break

        logger.info("Next check in %d minute(s).", config.scheduler.check_interval_minutes)

        for _ in range(interval_seconds):
            if not is_running():
                break
            time.sleep(1)

    tracker.close()
    logger.info("AI Pen Pal stopped.")
