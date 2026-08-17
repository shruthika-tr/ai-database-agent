from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.services import email_service
from app.services.database_service import execute_sql
from app.services.forecasting_service import (
    calculate_next_forecast_month,
    detect_forecast_intent,
    extract_country_from_message,
    generate_forecast,
)
from app.services.llm_service import explain_forecast, generate_sql, summarize_result
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

    # Check for forecast intent BEFORE SQL generation
    if detect_forecast_intent(message):
        country = extract_country_from_message(message)
        forecast_month = calculate_next_forecast_month()
        forecast_result = generate_forecast(country, forecast_month)

        if forecast_result.get("error"):
            raise ValueError(forecast_result["error"])

        prediction = forecast_result.get("prediction")
        num_months = forecast_result.get("num_months", 0)
        explanation = explain_forecast(
            message, country, forecast_month, prediction, num_months
        )

        return {
            "type": "forecast",
            "country": country,
            "period": forecast_month,
            "prediction": prediction,
            "message": explanation,
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
