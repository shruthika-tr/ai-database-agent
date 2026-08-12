from __future__ import annotations

import os
import re
from email.message import EmailMessage
from typing import Any

from aiosmtplib import SMTP
from dotenv import load_dotenv

from app.services.llm_service import summarize_result
from app.services.session_service import get_session

load_dotenv()


EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
REQUEST_WORDS = ("send", "email", "mail")


def extract_email(text: str) -> str | None:
    """Return the first plain email address from normal text or Markdown mail links.

    Args:
        text: The input text to scan for an email address.

    Returns:
        The plain email address, or None if no valid address is found.
    """
    if not text:
        return None

    candidates: list[str] = []

    for match in EMAIL_PATTERN.finditer(text):
        candidate = match.group(0).strip().strip("[]()")
        candidate = candidate.replace("mailto:", "").strip()
        if candidate:
            candidates.append(candidate)

    markdown_match = re.search(
        r"\[[^\]]*?([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\]\(mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\)",
        text,
        flags=re.IGNORECASE,
    )
    if markdown_match:
        candidates.append(markdown_match.group(1).strip())
        candidates.append(markdown_match.group(2).strip())

    mailto_match = re.search(r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text, flags=re.IGNORECASE)
    if mailto_match:
        candidates.append(mailto_match.group(1).strip())

    seen: set[str] = set()
    for candidate in candidates:
        normalized = candidate.strip("[]() ")
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            return normalized

    return None


def is_email_request(text: str) -> bool:
    """Check whether the text appears to be a request to send an email.

    The detection is intentionally simple: the text must contain an email address
    and at least one common request word such as "send", "email", or "mail".
    """
    if not text:
        return False

    email = extract_email(text)
    if email is None:
        return False

    normalized = text.lower()
    return any(word in normalized for word in REQUEST_WORDS)


def prepare_email_summary(session_id: str, user_message: str) -> dict[str, Any]:
    """Validate an email request and prepare the summary payload for delivery.

    The function checks whether the message contains an email request, extracts the
    recipient, loads the prior session, and generates a concise summary from the
    stored result. The SMTP send step is intentionally not implemented here.
    """
    if not is_email_request(user_message):
        raise ValueError("The message is not a valid email request.")

    recipient = extract_email(user_message)
    if recipient is None:
        raise ValueError("No recipient email address was found in the message.")

    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session '{session_id}' does not exist.")

    if session.last_result is None:
        raise ValueError(f"Session '{session_id}' has no previous result to summarize.")

    summary = summarize_result(session.last_question, session.last_result)

    return {
        "recipient": recipient,
        "subject": "AI Database Agent - Query Summary",
        "summary": summary,
        "session_id": session_id,
    }


async def send_email(recipient: str, subject: str, body: str) -> bool:
    """Send an email using Gmail SMTP with STARTTLS."""

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not smtp_host or not smtp_port or not smtp_username or not smtp_password:
        raise RuntimeError(
            "SMTP_HOST, SMTP_PORT, SMTP_USERNAME, and SMTP_PASSWORD "
            "environment variables are required."
        )

    try:
        port = int(smtp_port)
    except ValueError as exc:
        raise ValueError("SMTP_PORT must be an integer.") from exc

    message = EmailMessage()
    message["From"] = smtp_username
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    async with SMTP(
        hostname=smtp_host,
        port=port,
        start_tls=True,
    ) as smtp:
        await smtp.login(smtp_username, smtp_password)
        await smtp.send_message(message)

    return True