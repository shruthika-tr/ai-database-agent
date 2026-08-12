from __future__ import annotations

import json
import os
import re
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def _get_gemini_api_key() -> str:
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY environment variable is required for Gemini API access.')
    return api_key


def _create_gemini_client() -> genai.Client:
    return genai.Client(api_key=_get_gemini_api_key())


def generate_text(prompt: str, model: str = 'gemini-3.5-flash', temperature: float = 0.2, max_output_tokens: int = 512) -> str:
    """Send a prompt to Gemini and return the text response."""
    with _create_gemini_client() as client:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )

    return response.text


def _clean_sql_response(response: str) -> str:
    """Normalize Gemini SQL output by stripping code fences and surrounding whitespace."""
    cleaned = response.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
    if cleaned.startswith("`") and cleaned.endswith("`"):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _has_unmatched_quotes(sql: str) -> bool:
    """Return True if the SQL contains an odd number of single quotes."""
    return sql.count("'") % 2 != 0


def _is_incomplete_sql(sql: str) -> bool:
    """Return True if the SQL ends with an obviously incomplete clause."""
    normalized = sql.strip().rstrip(";").strip()
    if not normalized:
        return True

    if _has_unmatched_quotes(normalized):
        return True

    incomplete_patterns = [
        r"[<>=]\s*$",
        r"\bIN\s*$",
        r"\bAND\s*$",
        r"\bOR\s*$",
        r"\bWHERE\s*$",
        r"\bNOT\s*$",
    ]

    for pattern in incomplete_patterns:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return True

    return False


def generate_sql(question: str, schema: str, model: str = 'gemini-3.5-flash', temperature: float = 0.0, max_output_tokens: int = 512) -> str:
    """Generate a SQL SELECT statement from the question and database schema."""
    prompt = (
        "You are a SQL generator. Use only the provided database schema. "
        "Do not invent tables, columns, or values. Return only a single, complete, executable SQLite SELECT statement. "
        "The statement must start with SELECT and end with a semicolon. "
        "Every WHERE condition must include a column, comparison operator, and value. "
        "Never leave a comparison such as \"product =\" incomplete. "
        "Do not end the statement with a dangling AND, OR, or WHERE clause. "
        "Do not return Markdown, explanations, placeholders, or any text besides the SQL. "
        "Use only tables and columns from the supplied schema. "
        "When comparing text values from the user's question to database columns, prefer case-insensitive comparisons such as LOWER(column) = LOWER('value'). "
        "If the question refers to a specific product, preserve the user's text and compare it case-insensitively.\n\n"
        "Schema:\n"
        f"{schema}\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Examples:\n"
        "Question: What is the total sales amount in Germany?\n"
        "Expected SQL: SELECT SUM(total_amount) FROM sales WHERE country = 'Germany';\n"
        "Question: How many laptops were sold in India?\n"
        "Expected SQL: SELECT SUM(quantity) FROM sales WHERE LOWER(country) = LOWER('India') AND LOWER(product) = LOWER('laptops');\n"
        "Question: What is the average unit price of laptops?\n"
        "Expected SQL: SELECT AVG(unit_price) FROM sales WHERE LOWER(product) = LOWER('laptops');\n\n"
        "SQL:"
    )

    with _create_gemini_client() as client:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )

    sql = _clean_sql_response(response.text)
    if _is_incomplete_sql(sql):
        raise ValueError(
            "Generated SQL appears incomplete. The model must return a complete SELECT statement with all comparison values present."
        )

    return sql.strip()

def _normalize_question_to_statement(question: str) -> str:
    statement = question.strip()
    if statement.endswith("?"):
        statement = statement[:-1].strip()

    prefixes = [
        "what is ",
        "what are ",
        "how many ",
        "how much ",
        "which ",
        "who ",
        "where ",
        "when ",
    ]

    lower_statement = statement.lower()
    for prefix in prefixes:
        if lower_statement.startswith(prefix):
            statement = statement[len(prefix) :].strip()
            break

    if not statement.lower().startswith("the "):
        statement = "The " + statement

    return statement


def summarize_result(question: str, result: object, model: str = 'gemini-3.5-flash', temperature: float = 0.2, max_output_tokens: int = 256) -> str:
    """Summarize a database result into a short professional statement.

    The function intentionally uses the existing generate_text() helper to keep the
    Gemini client logic centralized and unchanged.
    """
    result_text = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    prompt = (
        "You are a professional business summary writer. Use ONLY the supplied question and exact result. "
        "Do not invent any information. "
        "Convert database field names such as SUM(total_amount), total_quantity, and average_price into natural wording based on the question. "
        "Keep every supplied numeric value exactly as provided. "
        "Write 1-2 professional sentences and return only the summary text. "
        "Do not include SQL field names, markdown, or labels like 'Summary:'.\n\n"
        f"Question: {question}\n\n"
        f"Result: {result_text}\n\n"
        "Answer:"
    )

    summary = generate_text(
        prompt,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    ).strip()

    def flatten_values(value: object) -> list[str]:
        items: list[str] = []

        if isinstance(value, dict):
            for item in value.values():
                items.extend(flatten_values(item))
        elif isinstance(value, list):
            for item in value:
                items.extend(flatten_values(item))
        elif value is not None:
            items.append(str(value))

        return items

    exact_values = [value for value in flatten_values(result) if value and any(ch.isdigit() for ch in value)]

    if exact_values and not all(value in summary for value in exact_values):
        statement = _normalize_question_to_statement(question)
        summary = f"{statement} is {exact_values[0]}."

    return summary.replace("Summary:", "").replace("Answer:", "").strip()
