import pytest
import pandas as pd
from app.ingest import SftpIngestionService


class MockApp:
    """
    Mock Flask App that functions as a context manager.
    Essential because the service uses 'with self.app.app_context():'
    """
    def app_context(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_normalization_csv():
    """Test that standard CSV files are normalized correctly."""
    service = SftpIngestionService(MockApp())

    csv_content = """TradeDate,AccountID,Ticker,Quantity,Price,TradeType,SettlementDate
2025-01-15,ACC001,AAPL,100,185.50,BUY,2025-01-17"""

    df = service.normalize_data(csv_content, "test.csv")

    assert df is not None
    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "AAPL"
    assert df.iloc[0]["quantity"] == 100
    assert str(df.iloc[0]["date"]) == "2025-01-15"


def test_normalization_pipe():
    """Test that Pipe-separated files are normalized correctly."""
    service = SftpIngestionService(MockApp())

    pipe_content = """REPORT_DATE|ACCOUNT_ID|SECURITY_TICKER|SHARES|MARKET_VALUE|TRANS_TYPE
20250115|ACC002|GOOGL|10|2000.00|BUY"""

    df = service.normalize_data(pipe_content, "test.dat")

    assert df is not None
    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "GOOGL"
    assert df.iloc[0]["quantity"] == 10
    assert df.iloc[0]["price"] == 200.00
    assert str(df.iloc[0]["date"]) == "2025-01-15"


def test_normalization_invalid():
    """Test that garbage data returns None gracefully."""
    service = SftpIngestionService(MockApp())

    garbage_content = "This is just random text\nWith no headers"

    df = service.normalize_data(garbage_content, "garbage.txt")

    assert df is None