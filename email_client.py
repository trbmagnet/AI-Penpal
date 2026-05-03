import email
import email.mime.multipart
import email.mime.text
import email.utils
import smtplib
import uuid
from datetime import datetime, timedelta
from email.header import decode_header

from imapclient import IMAPClient as IMAPClientLib

from config import EmailConfig
from email_parser import ParsedEmail, parse_email
from logger import setup_logger

logger = setup_logger()


class IMAPClient:
    def __init__(self, config: EmailConfig):
        self.config = config
        self._conn: IMAPClientLib | None = None

    def connect(self):
        logger.info("Connecting to IMAP server: %s:%s", self.config.imap_server, self.config.imap_port)
        self._conn = IMAPClientLib(self.config.imap_server, port=self.config.imap_port, ssl=True)
        self._conn.id_({"name": "ai_penpal", "version": "1.0.0"})
        self._conn.login(self.config.address, self.config.auth_password)
        logger.info("IMAP login successful")

    def fetch_recent_emails(self, ignore_older_than_minutes: int) -> list[tuple[str, email.message.Message]]:
        if not self._conn:
            raise RuntimeError("Not connected. Call connect() first.")

        self._conn.select_folder("INBOX")

        since_date = datetime.now() - timedelta(minutes=ignore_older_than_minutes)
        msg_ids = self._conn.search(["UNSEEN", "SINCE", since_date])

        if not msg_ids:
            logger.info("No new unseen emails found")
            return []

        logger.info("Found %d unseen email(s)", len(msg_ids))

        raw_messages = self._conn.fetch(msg_ids, ["RFC822"])
        parsed_emails = []
        for msg_id, data in raw_messages.items():
            raw_email = data[b"RFC822"]
            msg = email.message_from_bytes(raw_email)
            parsed_emails.append((str(msg_id), msg))

        return parsed_emails

    def disconnect(self):
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None


class SMTPSender:
    def __init__(self, config: EmailConfig):
        self.config = config
        self._conn: smtplib.SMTP | smtplib.SMTP_SSL | None = None

    def connect(self):
        logger.info("Connecting to SMTP server: %s:%s", self.config.smtp_server, self.config.smtp_port)
        if self.config.use_tls:
            self._conn = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port)
        else:
            self._conn = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            self._conn.starttls()
        self._conn.login(self.config.address, self.config.auth_password)
        logger.info("SMTP login successful")

    def send_reply(self, parsed_email: ParsedEmail, reply_body: str):
        if not self._conn:
            raise RuntimeError("Not connected. Call connect() first.")

        msg = email.mime.multipart.MIMEMultipart()
        msg["From"] = self.config.address
        msg["To"] = parsed_email.sender
        msg["Subject"] = f"Re: {parsed_email.subject}" if parsed_email.subject else "Re: (no subject)"
        msg["Reply-To"] = self.config.address

        new_message_id = f"<{uuid.uuid4()}@ai_penpal>"
        msg["Message-ID"] = new_message_id

        if parsed_email.message_id:
            msg["In-Reply-To"] = parsed_email.message_id
            refs = parsed_email.references.strip()
            if refs:
                msg["References"] = f"{refs} {parsed_email.message_id}"
            else:
                msg["References"] = parsed_email.message_id

        msg.attach(email.mime.text.MIMEText(reply_body, "plain", "utf-8"))

        self._conn.sendmail(
            self.config.address,
            parsed_email.sender,
            msg.as_string(),
        )
        logger.info("Reply sent to %s (Message-ID: %s)", parsed_email.sender, new_message_id)

    def disconnect(self):
        if self._conn:
            try:
                self._conn.quit()
            except Exception:
                pass
            self._conn = None
