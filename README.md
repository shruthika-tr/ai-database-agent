# AI-Powered Database Query & Email Agent

An AI-powered application that allows users to query sales data using natural language, generate business summaries, send results via email, and forecast future sales using machine learning.

## Features

- Natural language to SQL generation using Google Gemini
- SQL validation for safe, read-only database access
- SQLite database with SQLAlchemy
- AI-generated business summaries
- Email reports via SMTP
- Session-based query/result context
- ML-based sales forecasting using Linear Regression
- Global and country-specific sales forecasting
- Automated testing with pytest

## Architecture

User
│
▼
FastAPI
│
▼
AI Agent
├── Natural Language Query
│ └── Gemini → SQL → Validation → SQLite
│
├── Forecasting Request
│ └── Historical Sales → Linear Regression → Prediction
│
└── Email Request
└── Previous Result → Gemini Summary → SMTP → Email

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **LLM:** Google Gemini
- **Machine Learning:** Scikit-learn, Linear Regression
- **Database:** SQLite, SQLAlchemy
- **Email:** aiosmtplib
- **Frontend:** HTML, CSS, JavaScript
- **Testing:** pytest

## Project Structure

ai-database-agent/
├── app/
│ ├── main.py
│ ├── database.py
│ ├── models/
│ │ └── forecast_model.py
│ └── services/
│ ├── agent_service.py
│ ├── llm_service.py
│ ├── sql_service.py
│ ├── database_service.py
│ ├── email_service.py
│ ├── session_service.py
│ └── forecasting_service.py
│
├── static/
├── data/
│ └── sales.db
├── tests/
│ ├── test_sql_service.py
│ └── test_forecasting_service.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

## Setup

### 1. Clone the repository

git clone https://github.com/shruthika-tr/ai-database-agent.git
cd ai-database-agent

### 2. Create and activate virtual environment

python -m venv venv

.\venv\Scripts\Activate.ps1

### 3. Install dependencies

pip install -r requirements.txt

### 4. Configure environment variables

Create a `.env` file:

GEMINI_API_KEY=your_gemini_api_key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

### 5. Run the application

python -m uvicorn app.main:app --reload

Open:
http://127.0.0.1:8000/

## Example

**Database Query**

> What is the total sales amount in Germany?

**Forecasting**

> Predict India's sales for next month.

The system retrieves historical sales data and uses Linear Regression to generate the next month's sales forecast.

## Testing

Run the complete test suite:

python -m pytest -q

**Current result: 45 tests passed.**

## Security

- API keys and credentials are stored in environment variables.
- `.env` is excluded from Git.
- Only safe, read-only SQL queries are executed.
- Dangerous SQL operations and multiple statements are blocked.

## Author

**T R Shruthika**
