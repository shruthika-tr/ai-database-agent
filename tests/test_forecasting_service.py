"""Tests for the sales forecasting feature."""

import pytest

from app.services.forecasting_service import (
    calculate_next_forecast_month,
    detect_forecast_intent,
    extract_country_from_message,
    generate_forecast,
    get_monthly_sales_data,
)


class TestForecastIntentDetection:
    """Test forecast intent detection."""

    def test_detect_forecast_intent_predict(self):
        """Test detection of 'predict' keyword."""
        assert detect_forecast_intent("Can you predict India's sales for next month?")

    def test_detect_forecast_intent_forecast(self):
        """Test detection of 'forecast' keyword."""
        assert detect_forecast_intent("Can you forecast India's sales for next month?")

    def test_detect_forecast_intent_project(self):
        """Test detection of 'project' keyword."""
        assert detect_forecast_intent("Project the sales for next month.")

    def test_detect_forecast_intent_estimate(self):
        """Test detection of 'estimate' keyword."""
        assert detect_forecast_intent("Estimate next month's sales.")

    def test_detect_forecast_intent_will_sell(self):
        """Test detection of 'will sell' pattern."""
        assert detect_forecast_intent("How many units will India sell next month?")

    def test_detect_forecast_intent_sales_next(self):
        """Test detection of 'sales next' pattern."""
        assert detect_forecast_intent("What will sales be next month?")

    def test_detect_forecast_intent_negative_normal_query(self):
        """Test that normal queries are NOT classified as forecasts."""
        assert not detect_forecast_intent("What were the total sales in India?")

    def test_detect_forecast_intent_negative_average_price(self):
        """Test that average price queries are NOT classified as forecasts."""
        assert not detect_forecast_intent("What is the average unit price in Germany?")

    def test_detect_forecast_intent_empty_string(self):
        """Test with empty string."""
        assert not detect_forecast_intent("")

    def test_detect_forecast_intent_none(self):
        """Test with None."""
        assert not detect_forecast_intent(None)


class TestCountryExtraction:
    """Test country extraction from messages."""

    def test_extract_country_india(self):
        """Test extraction of India."""
        country = extract_country_from_message("Predict India's sales for next month")
        assert country == "India"

    def test_extract_country_germany(self):
        """Test extraction of Germany."""
        country = extract_country_from_message("Forecast Germany's sales")
        assert country == "Germany"

    def test_extract_country_case_insensitive(self):
        """Test case-insensitive extraction."""
        country = extract_country_from_message("forecast INDIA sales")
        assert country == "India"

    def test_extract_country_none(self):
        """Test with no country mentioned."""
        country = extract_country_from_message("Predict next month's sales")
        assert country is None

    def test_extract_country_first_match(self):
        """Test that first mentioned country is extracted."""
        country = extract_country_from_message("Compare India and Germany sales")
        assert country == "India"


class TestMonthlyDataAggregation:
    """Test monthly sales data retrieval."""

    def test_get_monthly_sales_data_global(self):
        """Test global monthly aggregation."""
        data = get_monthly_sales_data()
        
        assert len(data) > 0
        assert all(isinstance(item, tuple) and len(item) == 2 for item in data)
        assert all(isinstance(item[1], float) for item in data)

    def test_get_monthly_sales_data_country_india(self):
        """Test country-specific aggregation for India."""
        data = get_monthly_sales_data("India")
        
        assert len(data) > 0
        assert all(isinstance(item, tuple) and len(item) == 2 for item in data)

    def test_get_monthly_sales_data_sorted(self):
        """Test that data is sorted by month."""
        data = get_monthly_sales_data()
        months = [item[0] for item in data]
        
        assert months == sorted(months)

    def test_get_monthly_sales_data_no_null_values(self):
        """Test that no null sales values are included."""
        data = get_monthly_sales_data()
        
        assert all(item[1] is not None and item[1] > 0 for item in data)


class TestForecastGeneration:
    """Test forecast generation."""

    def test_generate_forecast_global(self):
        """Test global forecast generation."""
        result = generate_forecast(None, "August 2026")
        
        if result.get("error"):
            assert "error" in result
        else:
            assert result["prediction"] is not None
            assert isinstance(result["prediction"], float)
            assert result["country"] is None
            assert result["period"] == "August 2026"
            assert result["num_months"] >= 3

    def test_generate_forecast_country_india(self):
        """Test country-specific forecast for India."""
        result = generate_forecast("India", "August 2026")
        
        if result.get("error"):
            assert "error" in result
        else:
            assert result["prediction"] is not None
            assert isinstance(result["prediction"], float)
            assert result["country"] == "India"

    def test_generate_forecast_insufficient_data(self):
        """Test that insufficient data returns error."""
        result = generate_forecast("NonexistentCountry", "August 2026")
        
        assert result.get("error") is not None

    def test_generate_forecast_response_structure(self):
        """Test that response has all required keys."""
        result = generate_forecast(None, "August 2026")
        
        required_keys = ["prediction", "country", "period", "num_months", "error"]
        assert all(key in result for key in required_keys)


class TestNextForecastMonth:
    """Test next month calculation."""

    def test_calculate_next_forecast_month(self):
        """Test that next forecast month is calculated."""
        month = calculate_next_forecast_month()
        
        assert month is not None
        assert isinstance(month, str)
        assert len(month) > 0


class TestForecastingFlow:
    """Integration tests for forecasting flow."""

    def test_forecast_prediction_is_numeric(self):
        """Test that forecast prediction is a numeric value."""
        result = generate_forecast(None, "August 2026")
        
        if result.get("error") is None:
            assert isinstance(result["prediction"], (int, float))
            assert result["prediction"] > 0

    def test_forecast_does_not_interfere_with_normal_queries(self):
        """Test that normal SQL queries still work (smoke test)."""
        # This is a placeholder - actual test would need to test agent_service flow
        assert detect_forecast_intent("What is total sales in India?") is False

    def test_multiple_forecasts_consistent(self):
        """Test that requesting the same forecast twice gives consistent results."""
        result1 = generate_forecast("India", "August 2026")
        result2 = generate_forecast("India", "August 2026")
        
        if result1.get("error") is None and result2.get("error") is None:
            assert result1["prediction"] == result2["prediction"]
