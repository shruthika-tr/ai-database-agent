from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SessionState:
    """Holds the state for a single AI Database Agent session."""

    session_id: str
    last_question: str = ""
    last_sql: str = ""
    last_result: Any = None


_sessions: Dict[str, SessionState] = {}


def create_session(session_id: str) -> SessionState:
    """Create a new session state for the given session ID.

    If a session with the same ID already exists, it is replaced.
    """
    session = SessionState(session_id=session_id)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[SessionState]:
    """Return the session state for the given session ID, or None if missing."""
    return _sessions.get(session_id)


def update_session(session_id: str, question: str, sql: str, result: Any) -> SessionState:
    """Update an existing session or create a new one with the latest interaction.

    Args:
        session_id: Unique identifier for the session.
        question: The last question asked by the user.
        sql: The SQL generated in response to the question.
        result: The result returned from executing the SQL.

    Returns:
        The updated SessionState for the session.
    """
    session = _sessions.get(session_id)

    if session is None:
        session = create_session(session_id)

    session.last_question = question
    session.last_sql = sql
    session.last_result = result
    _sessions[session_id] = session

    return session
