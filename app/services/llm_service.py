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
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
        except Exception:
            # Surface a concise, non-sensitive error for upstream handling.
            raise RuntimeError(
                "LLM API request failed. Verify GEMINI_API_KEY, project access, and quota."
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
        "If the question asks for a total, count, average, or number of records, return an aggregate query that returns one row. "
        "Use SUM(total_amount) for total sales, total sales amount, total revenue, or how much sales questions. "
        "Use SUM(quantity) for how many items were sold, quantity sold, number of units sold, total quantity, or similar quantity/unit questions. "
        "Use AVG(unit_price) for average price or average unit price questions. "
        "Use COUNT(*) for number of sales, orders, or records questions. "
        "Do not choose COUNT(*) for questions asking how many units/products were sold unless the question explicitly asks for number of orders or records. "
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
        "Expected SQL: SELECT SUM(total_amount) FROM sales WHERE LOWER(country) = LOWER('Germany');\n"
        "Question: How many laptops were sold in India?\n"
        "Expected SQL: SELECT SUM(quantity) FROM sales WHERE LOWER(country) = LOWER('India') AND LOWER(product) = LOWER('laptops');\n"
        "Question: What quantity of laptops was sold in India?\n"
        "Expected SQL: SELECT SUM(quantity) FROM sales WHERE LOWER(country) = LOWER('India') AND LOWER(product) = LOWER('laptops');\n"
        "Question: How many units of laptops were sold in India?\n"
        "Expected SQL: SELECT SUM(quantity) FROM sales WHERE LOWER(country) = LOWER('India') AND LOWER(product) = LOWER('laptops');\n"
        "Question: What is the total quantity of laptops sold in India?\n"
        "Expected SQL: SELECT SUM(quantity) FROM sales WHERE LOWER(country) = LOWER('India') AND LOWER(product) = LOWER('laptops');\n"
        "Question: What is the average unit price of products sold in Germany?\n"
        "Expected SQL: SELECT AVG(unit_price) FROM sales WHERE LOWER(country) = LOWER('Germany');\n"
        "Question: How many sales were made in March 2026?\n"
        "Expected SQL: SELECT COUNT(*) FROM sales WHERE sale_date >= '2026-03-01' AND sale_date <= '2026-03-31';\n"
        "Question: What is the total revenue for keyboards in the UK?\n"
        "Expected SQL: SELECT SUM(total_amount) FROM sales WHERE LOWER(country) = LOWER('UK') AND LOWER(product) = LOWER('keyboards');\n"
        "Question: What were the total sales in January 2026?\n"
        "Expected SQL: SELECT SUM(total_amount) FROM sales WHERE sale_date >= '2026-01-01' AND sale_date <= '2026-01-31';\n\n"
        "SQL:"
    )

    with _create_gemini_client() as client:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
        except Exception:
            raise RuntimeError(
                "LLM API request failed. Verify GEMINI_API_KEY, project access, and quota."
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
        "You are a business insight writer. Use ONLY the supplied question and exact result. "
        "Return exactly two sentences. Sentence 1 should state the actual result clearly in natural business language. "
        "Sentence 2 should give one practical business recommendation relevant to the question and result. "
        "Return only the final two sentences with no headings, labels, prefixes, markdown, or explanations. "
        "Do not mention the prompt, LLM, SQL, database, schema, or instructions. "
        "Do not repeat the question. "
        "Do not invent any facts, trends, comparisons, percentages, or claims beyond the provided result. "
        "If the result is empty or null, say no matching data was found and recommend a reasonable next step.\n\n"
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

    def _clean_summary(text: str) -> str:
        cleaned = text.strip()
        for prefix in [
            "answer:",
            "summary:",
            "observation:",
            "recommendation:",
            "natural wording:",
            "analysis:",
        ]:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()
        return cleaned

    def _split_sentences(text: str) -> list[str]:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _format_value(value: object) -> str:
        if isinstance(value, float):
            formatted = f"{value:,.2f}"
            if "." in formatted:
                formatted = formatted.rstrip("0").rstrip(".")
            return formatted
        if isinstance(value, int):
            return f"{value:,}"
        return str(value)

    def _is_empty_result(value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False

    def _build_recommendation(question_text: str) -> str:
        lower = question_text.lower()
        sales_keywords = ["total sales", "sales amount", "total amount", "sales", "revenue"]
        quantity_keywords = ["quantity", "units sold", "unit sold", "units", "sold"]
        price_keywords = ["average unit price", "avg unit price", "average price", "avg price", "unit price"]
        count_keywords = ["count", "orders", "transactions", "order volume", "order count", "transaction count"]
        product_keywords = ["product", "products", "item", "items", "sku", "model", "category"]
        region_keywords = ["country", "region", "market", "state", "city", "territory"]

        if any(keyword in lower for keyword in price_keywords):
            return "Consider monitoring pricing and product demand to maintain competitive pricing."

        if any(keyword in lower for keyword in count_keywords):
            return "Consider monitoring order volume and operational capacity."

        if any(keyword in lower for keyword in quantity_keywords) and not any(keyword in lower for keyword in price_keywords):
            return "Consider maintaining sufficient stock and monitoring product demand."

        if any(keyword in lower for keyword in sales_keywords) and "average" not in lower:
            if any(keyword in lower for keyword in region_keywords):
                return "Consider monitoring demand in that market and maintaining appropriate inventory levels."
            if any(keyword in lower for keyword in product_keywords):
                return "Consider maintaining appropriate inventory levels for that product and monitoring its demand."
            return "Consider monitoring demand and maintaining appropriate inventory levels to support continued sales."

        if any(keyword in lower for keyword in product_keywords):
            return "Consider maintaining appropriate stock for that product and monitoring its demand."

        if any(keyword in lower for keyword in region_keywords):
            return "Consider monitoring demand in that market and maintaining appropriate inventory levels."

        return "Consider monitoring the relevant metric and adjusting operations to support the requested outcome."

    def _fallback_text(question_text: str, value: object) -> str:
        if _is_empty_result(value):
            return (
                "No matching data was found for the current query. "
                "Consider checking the filters or reviewing the requested criteria."
            )

        if isinstance(value, dict) and len(value) == 1:
            value = next(iter(value.values()))
        elif isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict) and len(value[0]) == 1:
            value = next(iter(value[0].values()))

        if isinstance(value, (int, float, str)):
            formatted_value = _format_value(value)
            statement = _normalize_question_to_statement(question_text)
            recommendation = _build_recommendation(question_text)
            return f"{statement} is {formatted_value} based on the current data. {recommendation}"

        return (
            "The result includes multiple values from the current data. "
            "Review the returned data to interpret the specific requested metrics."
        )

    summary = _clean_summary(summary)
    forbidden = [
        "answer:",
        "summary:",
        "observation:",
        "recommendation:",
        "natural wording:",
        "analysis:",
    ]
    normalized_summary = summary.strip()
    sentence_list = _split_sentences(normalized_summary)

    if (
        not normalized_summary
        or any(label in normalized_summary.lower() for label in forbidden)
        or len(sentence_list) != 2
    ):
        summary = _fallback_text(question, result)
    else:
        summary = normalized_summary

    if summary and summary[0].islower():
        summary = summary[0].upper() + summary[1:]

    return summary.strip()


def explain_forecast(
    question: str,
    country: str | None,
    forecast_month: str,
    prediction: float,
    num_months_used: int,
    model: str = 'gemini-3.5-flash',
    temperature: float = 0.2,
    max_output_tokens: int = 256,
) -> str:
    """Explain a machine-learning generated forecast using Gemini.

    The prediction value is provided by the ML model and must never be altered
    by the LLM. Gemini is only used to provide business context and recommendations.

    Args:
        question: Original user question
        country: Country for forecast (or None for global)
        forecast_month: Target forecast period
        prediction: ML-generated prediction value (float)
        num_months_used: Number of historical months used
        model: Gemini model name
        temperature: LLM temperature
        max_output_tokens: Max tokens for response

    Returns:
        Business-friendly 2-sentence explanation of the forecast
    """
    formatted_prediction = f"{prediction:,.2f}"

    prompt = (
        "You are a business analyst explaining a sales forecast generated by machine learning. "
        f"The ML-predicted sales value is: {formatted_prediction}. "
        "DO NOT change, alter, round, or invent this number under any circumstances. "
        "Respond with exactly 2 sentences: "
        "Sentence 1: State the forecast clearly using the exact prediction value. "
        "Sentence 2: Provide one practical business recommendation based on this forecast. "
        "Return ONLY the 2 sentences with no headings, labels, prefixes, or explanations. "
        "Do not invent trends, confidence scores, growth rates, or unsupported claims. "
        "Do not claim the forecast is guaranteed or certain.\n\n"
        f"Question: {question}\n"
        f"Country: {country or 'Global'}\n"
        f"Forecast Period: {forecast_month}\n"
        f"Prediction: {formatted_prediction}\n"
        f"Historical Months Used: {num_months_used}\n\n"
        "Explanation:"
    )

    try:
        explanation = generate_text(
            prompt,
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        ).strip()

        if not explanation:
            return _build_deterministic_forecast_explanation(
                country, forecast_month, formatted_prediction
            )

        if formatted_prediction not in explanation:
            return _build_deterministic_forecast_explanation(
                country, forecast_month, formatted_prediction
            )

        return explanation

    except Exception:
        return _build_deterministic_forecast_explanation(
            country, forecast_month, formatted_prediction
        )


def _build_deterministic_forecast_explanation(
    country: str | None, forecast_month: str, prediction_str: str
) -> str:
    """Build a forecast explanation without LLM when Gemini is unavailable.

    Args:
        country: Country for forecast (or None for global)
        forecast_month: Target forecast period
        prediction_str: Formatted prediction value

    Returns:
        Deterministic 2-sentence explanation
    """
    location = country or "overall"
    return (
        f"Based on historical sales data, the predicted sales for {location} in {forecast_month} are {prediction_str}. "
        f"Consider using this forecast to support inventory planning and business decisions for the upcoming month."
    )
