import email
import email.mime.multipart
import email.mime.text
from datetime import datetime, timezone

from email_parser import parse_email, ParsedEmail


def _make_simple_email(from_addr, subject, body, message_id="<test@example.com>"):
    msg = email.mime.text.MIMEText(body, "plain", "utf-8")
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
    return msg


def test_parse_simple_email():
    msg = _make_simple_email(
        "Alice <alice@example.com>",
        "Hello",
        "Hi there!",
        "<abc@def.com>",
    )
    parsed = parse_email(msg)
    assert parsed.sender == "alice@example.com"
    assert parsed.sender_name == "Alice"
    assert parsed.subject == "Hello"
    assert parsed.body == "Hi there!"
    assert parsed.message_id == "<abc@def.com>"
    assert parsed.date is not None


def test_parse_multipart_email():
    msg = email.mime.multipart.MIMEMultipart()
    msg["From"] = "Bob <bob@example.com>"
    msg["Subject"] = "Multipart"
    msg["Message-ID"] = "<multi@test.com>"
    msg["Date"] = "Tue, 02 Jan 2024 12:00:00 +0000"

    text_part = email.mime.text.MIMEText("Plain text body", "plain", "utf-8")
    html_part = email.mime.text.MIMEText("<p>HTML body</p>", "html", "utf-8")
    msg.attach(text_part)
    msg.attach(html_part)

    parsed = parse_email(msg)
    assert parsed.body == "Plain text body"


def test_parse_chinese_email():
    msg = email.mime.text.MIMEText("你好世界", "plain", "utf-8")
    msg["From"] = "测试 <test@example.com>"
    msg["Subject"] = "测试邮件"
    msg["Message-ID"] = "<zhongwen@test.com>"
    msg["Date"] = "Wed, 03 Jan 2024 12:00:00 +0000"

    parsed = parse_email(msg)
    assert parsed.body == "你好世界"
    assert parsed.subject == "测试邮件"


def test_parse_email_no_body():
    msg = email.mime.text.MIMEText("", "plain", "utf-8")
    msg["From"] = "Empty <empty@example.com>"
    msg["Subject"] = "Empty"
    msg["Message-ID"] = "<empty@test.com>"

    parsed = parse_email(msg)
    assert parsed.body == ""


def test_parse_email_no_subject():
    msg = email.mime.text.MIMEText("Body only", "plain", "utf-8")
    msg["From"] = "NoSubject <nosubject@example.com>"
    msg["Message-ID"] = "<nosubj@test.com>"

    parsed = parse_email(msg)
    assert parsed.subject == ""
    assert parsed.body == "Body only"
