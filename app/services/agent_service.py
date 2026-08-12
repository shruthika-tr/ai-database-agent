from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.services import email_service
from app.services.database_service import execute_sql
from app.services.llm_service import generate_sql, summarize_result
from app.services.session_service import get_session, update_session
from app.services.sql_service import validate_select_sql


def process_message(message: str, session_id: str, schema: str) -> Dict[str, Any]:
    """Process a user message either as an email request or a database query."""
    # Enhanced email request handling:
    # If the user message contains an email-request verb (send/email/mail) treat
    # it as an email intent even when extract_email() returns None so we can
    # validate and reject invalid addresses like "Send this summary to hello".
    normalized = (message or "").lower()
    contains_request_word = any(w in normalized for w in ("send", "email", "mail"))

    if contains_request_word:
        recipient = email_service.extract_email(message)
        if recipient is None:
            # The user requested sending but did not supply a valid email address.
            raise ValueError("Please provide a valid email address.")

        session = get_session(session_id)
        if session is None or session.last_result is None:
            raise ValueError("No previous session result is available to email.")

        summary = summarize_result(session.last_question, session.last_result)
        subject = "AI Database Agent - Query Summary"

        try:
            send_email_result = asyncio.run(
                email_service.send_email(recipient, subject, summary)
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to send email: {exc}") from exc

        if not send_email_result:
            raise RuntimeError("Failed to send email for an unknown reason.")

        return {
            "type": "email",
            "recipient": recipient,
            "summary": summary,
            "message": "Summary emailed successfully.",
        }

    sql = generate_sql(message, schema)
    validate_select_sql(sql)
    result = execute_sql(sql)
    summary = summarize_result(message, result)
    update_session(session_id, message, sql, result)

    return {
        "type": "query",
        "question": message,
        "sql": sql,
        "result": result,
        "summary": summary,
    }
