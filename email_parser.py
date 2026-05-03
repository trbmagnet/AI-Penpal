import email
import email.header
import email.message
import email.utils
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AttachmentInfo:
    filename: str
    content_type: str
    size: int


@dataclass
class ParsedEmail:
    message_id: str
    sender: str
    sender_name: str
    subject: str
    date: datetime | None
    body: str
    attachments: list[AttachmentInfo] = field(default_factory=list)
    references: str = ""
    in_reply_to: str = ""


def _decode_header(header_value: str | None) -> str:
    if not header_value:
        return ""
    decoded_parts = email.header.decode_header(header_value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        text_parts = []
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    text_parts.append(payload.decode(charset, errors="replace"))
        if text_parts:
            return "\n".join(text_parts)
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue
            if content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        return ""
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
        return ""


def _extract_attachments(msg: email.message.Message) -> list[AttachmentInfo]:
    attachments = []
    if not msg.is_multipart():
        return attachments
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in content_disposition or "inline" in content_disposition:
            filename = _decode_header(part.get_filename())
            if filename:
                content_type = part.get_content_type()
                payload = part.get_payload(decode=True)
                size = len(payload) if payload else 0
                attachments.append(
                    AttachmentInfo(
                        filename=filename,
                        content_type=content_type,
                        size=size,
                    )
                )
    return attachments


def parse_email(raw_msg: email.message.Message) -> ParsedEmail:
    message_id = raw_msg.get("Message-ID", "")
    sender = raw_msg.get("From", "")
    sender_name, sender_email = email.utils.parseaddr(sender)
    if not sender_name:
        sender_name = sender_email
    subject = _decode_header(raw_msg.get("Subject"))
    date_str = raw_msg.get("Date")
    date = None
    if date_str:
        date = email.utils.parsedate_to_datetime(date_str)
    body = _extract_body(raw_msg)
    attachments = _extract_attachments(raw_msg)
    references = raw_msg.get("References", "")
    in_reply_to = raw_msg.get("In-Reply-To", "")

    return ParsedEmail(
        message_id=message_id,
        sender=sender_email,
        sender_name=sender_name,
        subject=subject,
        date=date,
        body=body,
        attachments=attachments,
        references=references,
        in_reply_to=in_reply_to,
    )
