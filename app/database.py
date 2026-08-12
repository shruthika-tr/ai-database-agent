from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
DATABASE_URL = f"sqlite:///{DATA_DIR / 'sales.db'}"

DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class Sales(Base):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(100), nullable=False)
    product = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    sale_date = Column(Date, nullable=False)


def create_sales_table() -> None:
    """Create the sales table in the SQLite database."""
    Base.metadata.create_all(bind=engine)


def seed_sales_data() -> None:
    """Insert 40 realistic sales records into the sales table."""
    create_sales_table()

    sample_entries = [
        ('Germany', 'Laptop', 2, 1199.99, date(2026, 1, 4)),
        ('India', 'Mouse', 12, 24.50, date(2026, 1, 7)),
        ('France', 'Keyboard', 6, 54.99, date(2026, 1, 12)),
        ('USA', 'Monitor', 3, 249.99, date(2026, 1, 18)),
        ('UK', 'Laptop', 1, 1299.00, date(2026, 1, 22)),
        ('Japan', 'Mouse', 22, 19.99, date(2026, 1, 25)),
        ('Canada', 'Keyboard', 8, 59.99, date(2026, 2, 1)),
        ('Germany', 'Monitor', 4, 229.99, date(2026, 2, 5)),
        ('India', 'Laptop', 5, 1099.00, date(2026, 2, 9)),
        ('France', 'Mouse', 18, 22.99, date(2026, 2, 14)),
        ('USA', 'Keyboard', 9, 64.50, date(2026, 2, 18)),
        ('UK', 'Monitor', 2, 279.99, date(2026, 2, 23)),
        ('Japan', 'Laptop', 3, 1249.50, date(2026, 3, 2)),
        ('Canada', 'Mouse', 20, 17.99, date(2026, 3, 6)),
        ('Germany', 'Keyboard', 7, 49.99, date(2026, 3, 10)),
        ('India', 'Monitor', 6, 239.00, date(2026, 3, 15)),
        ('France', 'Laptop', 4, 1349.00, date(2026, 3, 20)),
        ('USA', 'Mouse', 30, 18.50, date(2026, 3, 24)),
        ('UK', 'Keyboard', 10, 69.99, date(2026, 4, 1)),
        ('Japan', 'Monitor', 5, 259.00, date(2026, 4, 5)),
        ('Canada', 'Laptop', 2, 1199.00, date(2026, 4, 10)),
        ('Germany', 'Mouse', 25, 21.50, date(2026, 4, 14)),
        ('India', 'Keyboard', 11, 57.99, date(2026, 4, 18)),
        ('France', 'Monitor', 3, 269.99, date(2026, 4, 23)),
        ('USA', 'Laptop', 6, 1399.00, date(2026, 5, 1)),
        ('UK', 'Mouse', 14, 23.99, date(2026, 5, 5)),
        ('Japan', 'Keyboard', 12, 52.50, date(2026, 5, 11)),
        ('Canada', 'Monitor', 7, 224.99, date(2026, 5, 17)),
        ('Germany', 'Laptop', 3, 1299.99, date(2026, 5, 22)),
        ('India', 'Mouse', 28, 16.99, date(2026, 5, 26)),
        ('France', 'Keyboard', 5, 62.00, date(2026, 6, 2)),
        ('USA', 'Monitor', 8, 249.00, date(2026, 6, 7)),
        ('UK', 'Laptop', 4, 1199.50, date(2026, 6, 12)),
        ('Japan', 'Mouse', 19, 20.99, date(2026, 6, 16)),
        ('Canada', 'Keyboard', 9, 55.99, date(2026, 6, 21)),
        ('Germany', 'Monitor', 3, 239.50, date(2026, 6, 26)),
        ('India', 'Laptop', 7, 1129.00, date(2026, 7, 2)),
        ('France', 'Mouse', 16, 18.75, date(2026, 7, 7)),
        ('USA', 'Keyboard', 13, 66.00, date(2026, 7, 12)),
        ('UK', 'Monitor', 4, 279.50, date(2026, 7, 17)),
        ('Japan', 'Laptop', 1, 1499.00, date(2026, 7, 22)),
    ]

    records = [
        Sales(
            country=country,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=quantity * unit_price,
            sale_date=sale_date,
        )
        for country, product, quantity, unit_price, sale_date in sample_entries
    ]

    with SessionLocal() as session:
        session.add_all(records)
        session.commit()


if __name__ == "__main__":
    seed_sales_data()
