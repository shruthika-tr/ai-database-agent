from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.database import engine


def detect_forecast_intent(message: str) -> bool:
    """Detect if the user is asking for a sales forecast or prediction."""
    if not message:
        return False

    normalized = message.lower()
    forecast_keywords = [
        "predict",
        "forecast",
        "project",
        "estimate",
        "will.*sell",
        "sales.*next",
        "next.*sales",
    ]

    for keyword in forecast_keywords:
        if re.search(keyword, normalized):
            return True

    return False


def extract_country_from_message(message: str) -> str | None:
    """Extract a country name from the user's message if present."""
    if not message:
        return None

    known_countries = [
        "India",
        "Germany",
        "France",
        "USA",
        "UK",
        "Japan",
        "Canada",
    ]

    for country in known_countries:
        if re.search(rf"\b{country}\b", message, re.IGNORECASE):
            return country

    return None


def calculate_next_forecast_month() -> str:
    """Calculate the next month based on the latest sale date in the database.
    
    Returns format: "2026-08" or "August 2026"
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT MAX(sale_date) as latest_date FROM sales")
            )
            row = result.fetchone()
            if row and row[0]:
                latest_date = row[0]
                if isinstance(latest_date, str):
                    latest_date = datetime.strptime(latest_date, "%Y-%m-%d").date()
                
                next_month = latest_date.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                
                return next_month.strftime("%B %Y")
            
            return "next month"
    except Exception:
        return "next month"


def get_monthly_sales_data(country: str | None = None) -> list[tuple[str, float]]:
    """Retrieve monthly aggregated sales from the database.
    
    Returns: List of (month_str, total_sales) tuples sorted by month.
    Example: [("2026-01", 5512.67), ("2026-02", 8449.18), ...]
    """
    try:
        query = """
        SELECT strftime('%Y-%m', sale_date) as month, SUM(total_amount) as sales
        FROM sales
        """

        if country:
            query += f" WHERE LOWER(country) = LOWER('{country}')"

        query += " GROUP BY month ORDER BY month"

        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = result.fetchall()

        if not rows:
            return []

        monthly_data = [(row[0], float(row[1])) for row in rows if row[0] and row[1]]
        return monthly_data

    except Exception as e:
        raise RuntimeError(f"Failed to retrieve monthly sales data: {e}")


def generate_forecast(
    country: str | None, forecast_month: str
) -> dict[str, Any]:
    """Generate a sales forecast using historical data and Linear Regression.
    
    Args:
        country: Optional country name for country-specific forecast
        forecast_month: Target month for forecast (e.g., "August 2026")
    
    Returns:
        Dict with keys:
        - prediction: float (the ML-generated forecast value)
        - country: str | None
        - period: str (formatted forecast month)
        - num_months: int (number of historical months used)
        - error: str | None (error message if forecast failed)
    """
    try:
        monthly_data = get_monthly_sales_data(country)

        if not monthly_data:
            return {
                "prediction": None,
                "country": country,
                "period": forecast_month,
                "num_months": 0,
                "error": f"No historical sales data available for {country or 'global'} forecast.",
            }

        if len(monthly_data) < 3:
            return {
                "prediction": None,
                "country": country,
                "period": forecast_month,
                "num_months": len(monthly_data),
                "error": f"Insufficient historical data ({len(monthly_data)} months) for reliable forecasting. At least 3 months required.",
            }

        from app.models.forecast_model import (
            train_linear_forecast_model,
            predict_next_month,
        )

        model = train_linear_forecast_model(monthly_data)
        prediction = predict_next_month(model, len(monthly_data))

        return {
            "prediction": prediction,
            "country": country,
            "period": forecast_month,
            "num_months": len(monthly_data),
            "error": None,
        }

    except Exception as e:
        return {
            "prediction": None,
            "country": country,
            "period": forecast_month,
            "num_months": 0,
            "error": f"Forecasting error: {str(e)}",
        }
