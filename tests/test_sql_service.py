import pytest

from app.services.sql_service import is_safe_select_sql, validate_select_sql


VALID_QUERIES = [
    "SELECT SUM(total_amount) FROM sales WHERE country = 'Germany';",
    "SELECT SUM(quantity) FROM sales WHERE country = 'India';",
    "SELECT AVG(unit_price) FROM sales WHERE country = 'France';",
    "SELECT * FROM sales LIMIT 10;",
]

DANGEROUS_QUERIES = [
    "SELECT * FROM sales; DROP TABLE sales;",
    "DELETE FROM sales WHERE id=1;",
    "UPDATE sales SET quantity=0;",
    "INSERT INTO sales VALUES (1,'x','y',1,1.0);",
    "DROP TABLE sales;",
    "CREATE TABLE evil(id INTEGER);",
    "PRAGMA writable_schema = 1;",
    "ATTACH DATABASE 'file.db' AS other;",
    "VACUUM;",
    "SELECT * FROM sqlite_master;",
]

MALFORMED_QUERIES = [
    "",
    "SELECT * FROM sales WHERE product =",
    "SELECT * FROM sales WHERE country = 'India' AND",
    "SELECT * FROM sales WHERE product IN (",
]


@pytest.mark.parametrize("sql", VALID_QUERIES)
def test_valid_select_queries(sql):
    # is_safe_select_sql should return True and validate_select_sql should not raise
    assert is_safe_select_sql(sql) is True
    # should not raise
    validate_select_sql(sql)


@pytest.mark.parametrize("sql", DANGEROUS_QUERIES)
def test_dangerous_queries_rejected(sql):
    # is_safe_select_sql should return False for dangerous queries
    assert is_safe_select_sql(sql) is False
    with pytest.raises(ValueError):
        validate_select_sql(sql)


@pytest.mark.parametrize("sql", MALFORMED_QUERIES)
def test_malformed_queries_rejected(sql):
    # malformed or empty SQL should be rejected
    assert is_safe_select_sql(sql) is False
    with pytest.raises(ValueError):
        validate_select_sql(sql)
