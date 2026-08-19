# AI-Powered Database Query & Email Agent

An AI-powered application that allows users to query sales data using natural language, generate business summaries, send results via email, and forecast future sales using machine learning.

## Features

- Natural language to SQL generation using Google Gemini
- SQL safety validation before execution
- Read-only SQLite database queries
- SQLAlchemy database integration
- AI-generated business summaries
- Email delivery using SMTP
- Session-based query and result context
- ML-based sales forecasting using Linear Regression
- Global and country-specific sales forecasting
- Automated testing with pytest

## Architecture

```
User
 │
 ▼
FastAPI
 │
 ▼
AI Agent
 ├── Natural Language Query
 │    └── Gemini → SQL → Validation → SQLite
 │
 ├── Forecasting Request
 │    └── Historical Sales → Linear Regression → Prediction
 │
 └── Email Request
      └── Previous Result → Gemini Summary → SMTP → Email
```

## Tech Stack

| Component        | Technology                      |
| ---------------- | ------------------------------- |
| Backend          | Python, FastAPI, Uvicorn        |
| LLM              | Google Gemini                   |
| Machine Learning | Scikit-learn, Linear Regression |
| Database         | SQLite, SQLAlchemy              |
| Email            | aiosmtplib                      |
| Frontend         | HTML, CSS, JavaScript           |
| Testing          | pytest                          |

## Project Structure

```
ai-database-agent/
│
├── app/
│   ├── main.py
│   ├── database.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── forecast_model.py
│   │
│   └── services/
│       ├── agent_service.py
│       ├── llm_service.py
│       ├── sql_service.py
│       ├── database_service.py
│       ├── email_service.py
│       ├── session_service.py
│       └── forecasting_service.py
│
├── static/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── data/
│   └── sales.db
│
├── tests/
│   ├── test_sql_service.py
│   └── test_forecasting_service.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the Repository

    git clone https://github.com/shruthika-tr/ai-database-agent.git
    cd ai-database-agent

### 2. Create a Virtual Environment

    python -m venv venv

Activate the virtual environment on Windows PowerShell:

    .\venv\Scripts\Activate.ps1

### 3. Install Dependencies

    pip install -r requirements.txt

### 4. Configure Environment Variables

Create a `.env` file in the project root:

    GEMINI_API_KEY=your_gemini_api_key

    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USERNAME=your_email@gmail.com
    SMTP_PASSWORD=your_app_password

Do not commit `.env` or any API keys or passwords to the repository.

### 5. Run the Application

    python -m uvicorn app.main:app --reload

Open the application at:

    http://127.0.0.1:8000/

## Example

### Natural Language Query

**User:**

> What is the total sales amount in Germany?

**Agent:**

> Total sales in Germany: $12,500

### Sales Forecasting

**User:**

> Predict India's sales for next month.

**Agent:**

> Predicted sales for India in August 2026: $X,XXX

The system retrieves historical sales data and uses a Linear Regression model to generate the next month's sales forecast.

## ML Sales Forecasting

The application uses historical monthly sales data to predict future sales.

### Forecasting Flow

```
User Forecasting Request
        │
        ▼
Forecast Intent Detection
        │
        ▼
Country Extraction
        │
        ▼
Historical Sales Retrieval
        │
        ▼
Monthly Sales Aggregation
        │
        ▼
Linear Regression Model
        │
        ▼
Next Month Prediction
```

The forecasting system supports:

- Global sales forecasting
- Country-specific sales forecasting
- Automatic forecast intent detection
- Historical monthly sales aggregation
- Next-month sales prediction

At least three months of historical sales data are required for forecasting.

## SQL Safety

LLM-generated SQL is treated as untrusted input and validated before execution.

The SQL validator allows only safe, read-only queries and rejects:

- Non-SELECT statements
- Multiple SQL statements
- INSERT
- UPDATE
- DELETE
- DROP
- CREATE
- ALTER
- TRUNCATE
- PRAGMA
- ATTACH
- VACUUM
- SQLite internal table access
- Malformed SQL

## Email Workflow

```
User Query
    │
    ▼
SQL Generation
    │
    ▼
SQL Validation
    │
    ▼
SQLite Execution
    │
    ▼
Result Display
    │
    ▼
User Email Request
    │
    ▼
Previous Result
    │
    ▼
Gemini Summary
    │
    ▼
SMTP
    │
    ▼
Email
```

## Testing

The project includes automated tests for SQL validation and ML forecasting.

Run the complete test suite:

    python -m pytest -q

**Current test result: 45 tests passed**

### Test Coverage

**SQL Validation**

- Valid SELECT queries
- Aggregate queries
- Dangerous SQL commands
- Multiple SQL statements
- SQLite internal table access
- Malformed SQL
- Incomplete SQL conditions

**ML Forecasting**

- Forecast intent detection
- Country extraction
- Monthly sales aggregation
- Global forecasting
- Country-specific forecasting
- Insufficient data handling
- Forecast response validation
- Next forecast month calculation
- Prediction consistency

## Security

- API keys and credentials are stored in environment variables.
- `.env` is excluded from Git.
- Only safe, read-only SQL queries are executed.
- Dangerous SQL operations are blocked.
- Multiple SQL statements are rejected.

## Future Improvements

- Advanced forecasting models
- Forecast visualization
- Multi-month forecasting
- Forecast confidence intervals
- Model performance evaluation
- Docker and cloud deployment

## Author

**T R Shruthika**
