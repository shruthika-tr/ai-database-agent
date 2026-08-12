import re

FORBIDDEN_SQL_KEYWORDS = re.compile(
    r"\b(?:insert|update|delete|drop|alter|create|truncate|pragma|attach|vacuum)\b",
    re.IGNORECASE,
)
SELECT_STATEMENT_RE = re.compile(r"^select\b", re.IGNORECASE)
STRING_LITERAL_RE = re.compile(r"('(?:''|[^'])*'|\"(?:\"\"|[^\"])*\")")
COMMENT_RE = re.compile(r"--.*?$|/\*.*?\*/", re.DOTALL | re.MULTILINE)


def _normalize_sql(sql: str) -> str:
    """Normalize SQL text for lightweight validation checks."""
    normalized = sql.strip()

    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip()

    normalized = STRING_LITERAL_RE.sub(" ", normalized)
    normalized = COMMENT_RE.sub(" ", normalized)
    normalized = normalized.lower()
    normalized = " ".join(normalized.split())
    return normalized


def is_safe_select_sql(sql: str) -> bool:
    """Return True if SQL is a single safe SELECT statement for SQLite."""
    if not sql or not sql.strip():
        return False

    normalized = _normalize_sql(sql)
    if not normalized:
        return False

    if ";" in normalized:
        # More than one statement or a stray semicolon is not allowed.
        return False

    # Reject references to internal SQLite meta tables.
    if any(internal in normalized for internal in ("sqlite_master", "sqlite_schema", "sqlite_temp_master")):
        return False

    # Reject unbalanced parentheses which indicate malformed SQL.
    if normalized.count("(") != normalized.count(")"):
        return False

    # For checks that depend on whether a literal value is present (e.g. a
    # dangling '=' or an incomplete IN list) inspect the original SQL after
    # removing comments but BEFORE stripping string literals — otherwise a
    # valid quoted value will be removed and produce a false-positive.
    raw = sql.strip()
    if raw.endswith(";"):
        raw = raw[:-1].rstrip()
    raw_no_comments = COMMENT_RE.sub(" ", raw)
    raw_no_comments = " ".join(raw_no_comments.split()).lower()

    # Reject dangling comparison operators or incomplete IN lists against
    # the raw SQL (with literals still present).
    if re.search(r"(?:=|<>|!=|<=|>=|<|>|like)\s*$", raw_no_comments):
        return False

    if re.search(r"\bin\s*\(\s*$", raw_no_comments):
        return False

    # Reject WHERE clauses ending with AND/OR or other dangling boolean operators.
    if re.search(r"\b(and|or)\s*$", raw_no_comments):
        return False

    if FORBIDDEN_SQL_KEYWORDS.search(normalized):
        return False

    if not SELECT_STATEMENT_RE.match(normalized):
        return False

    return True


def validate_select_sql(sql: str) -> None:
    """Raise ValueError if the SQL is not a safe single SELECT statement."""
    if not is_safe_select_sql(sql):
        raise ValueError(
            "Unsafe SQL detected. Only a single SELECT statement is permitted, "
            "and write or schema-modifying statements are rejected."
        )
