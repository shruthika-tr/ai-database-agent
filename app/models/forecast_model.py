from __future__ import annotations

from sklearn.linear_model import LinearRegression


def train_linear_forecast_model(
    monthly_data: list[tuple[str, float]],
) -> LinearRegression:
    """Train a Linear Regression model on monthly sales data.
    
    Args:
        monthly_data: List of (month_str, sales) tuples
        
    Returns:
        Trained LinearRegression model
    """
    if not monthly_data or len(monthly_data) < 2:
        raise ValueError("Need at least 2 months of data to train a forecast model")

    X = [[i + 1] for i in range(len(monthly_data))]
    y = [sales for _, sales in monthly_data]

    model = LinearRegression()
    model.fit(X, y)

    return model


def predict_next_month(model: LinearRegression, num_months: int) -> float:
    """Predict sales for the next month using a trained model.
    
    Args:
        model: Trained LinearRegression model
        num_months: Number of historical months (to predict month num_months + 1)
        
    Returns:
        Predicted sales value as float
    """
    next_month_num = num_months + 1
    prediction = model.predict([[next_month_num]])[0]
    
    return float(prediction)
