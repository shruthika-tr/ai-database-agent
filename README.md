```markdown
# AI-Powered Database Query & Email Agent

An AI-powered application that allows users to query sales data using natural language and email a business-friendly summary of the query result.

## Overview

The application converts natural-language questions into SQL queries using Google Gemini, validates the generated SQL, executes the query against a SQLite database, and displays the result.

Users can then request the previous result to be summarized and sent to an email address through SMTP.

## Features

- Natural language to SQL query generation
- SQL safety validation before execution
- Read-only SQLite database queries
- SQLAlchemy database integration
- AI-generated business summaries
- Email delivery using SMTP
- Session-based previous query/result context
- Simple web-based chat interface
- Automated SQL validator tests using pytest

## Example

### Database Query

**User:**

> What is the total sales amount in Germany?

**Agent:**

> Total Sales in Germany: $12,500

### Email Request

**User:**

> Send this summary to john@example.com

The agent generates a concise business-friendly summary of the previous result and sends it to the requested email address.

## Architecture

User
│
▼
FastAPI Application
│
▼
AI Agent
│
├── Natural Language Query
│ │
│ ▼
│ Gemini LLM
│ │
│ ▼
│ SQL Generation
│ │
│ ▼
│ SQL Validation
│ │
│ ▼
│ SQLAlchemy
│ │
│ ▼
│ SQLite
│ │
│ ▼
│ Query Result
│
└── Email Request
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

## Tech Stack

- **Language:** Python
- **Backend:** FastAPI, Uvicorn
- **LLM:** Google Gemini
- **Database:** SQLite
- **Database Access:** SQLAlchemy
- **Email:** aiosmtplib
- **Environment Variables:** python-dotenv
- **Testing:** pytest
- **Frontend:** HTML, CSS, JavaScript

## Project Structure

ai-database-agent/
│
├── app/
│ ├── main.py
│ ├── database.py
│ │
│ └── services/
│ ├── agent_service.py
│ ├── llm_service.py
│ ├── sql_service.py
│ ├── database_service.py
│ ├── email_service.py
│ └── session_service.py
│
├── static/
│ ├── index.html
│ ├── style.css
│ └── script.js
│
├── data/
│ └── sales.db
│
├── tests/
│ └── test_sql_service.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

## Prerequisites

- Python 3.11+
- Gemini API key
- SMTP-enabled email account

## Installation

### 1. Clone the repository

git clone https://github.com/shruthika-tr/ai-database-agent
cd ai-database-agent

### 2. Create a virtual environment

**Windows PowerShell:**

python -m venv venv

Activate it:

.\venv\Scripts\Activate.ps1

### 3. Install dependencies

pip install -r requirements.txt

## Environment Variables

Create a `.env` file in the project root.

Use `.env.example` as a reference:

GEMINI_API_KEY=your_gemini_api_key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

**Do not commit `.env` or any API keys/passwords to the repository.**

## Running the Application

Start the FastAPI server:

python -m uvicorn app.main:app --reload

Open the application in your browser:

http://127.0.0.1:8000/

## Database

The application uses SQLite for storing sales data.

SQLAlchemy is used for database access and query execution.

The database is located at:

data/sales.db

## SQL Safety

LLM-generated SQL is treated as untrusted input and is validated before execution.

The SQL validator ensures that only safe, read-only queries are executed.

The validator rejects:

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
- Malformed or incomplete SQL

## Email Workflow

User Query
↓
SQL Generation
↓
SQL Validation
↓
SQLite Execution
↓
Result Display
↓
User Email Request
↓
Previous Result
↓
AI Summary Generation
↓
SMTP
↓
Email

The application extracts the recipient email address, generates a concise summary of the previous query result, and sends it through SMTP.

## Testing

The project includes automated tests for SQL validation using pytest.

Run the tests with:

python -m pytest -q

Current test result:

18 passed

The test suite covers:

- Valid SELECT queries
- Aggregate queries
- Dangerous SQL commands
- Multiple SQL statements
- SQLite internal table access
- Malformed SQL
- Incomplete SQL conditions

## Author

**T R Shruthika**
```
