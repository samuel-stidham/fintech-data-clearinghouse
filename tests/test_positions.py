from app import db
from app.models import Trade


def test_positions_success(client, seed_data):
    """
    Test calculation of asset allocation percentages.
    """
    response = client.get("/positions?date=2025-01-15")
    assert response.status_code == 200

    data = response.json

    assert "ACC001" in data
    assert "ACC002" in data

    assert data["ACC001"]["AAPL"] == "100.0%"
    assert data["ACC002"]["GOOG"] == "100.0%"


def test_positions_mixed_allocation(client, app):
    """Test a more complex scenario with multiple tickers per account."""

    with app.app_context():
        t1 = Trade(
            trade_date="2025-02-01",
            account="ACC_MIX",
            ticker="A",
            quantity=10,
            price=20.00,
        )
        t2 = Trade(
            trade_date="2025-02-01",
            account="ACC_MIX",
            ticker="B",
            quantity=10,
            price=80.00,
        )
        db.session.add_all([t1, t2])
        db.session.commit()

    response = client.get("/positions?date=2025-02-01")
    assert response.status_code == 200
    data = response.json

    assert data["ACC_MIX"]["A"] == "20.0%"
    assert data["ACC_MIX"]["B"] == "80.0%"


def test_positions_empty_date(client):
    response = client.get("/positions?date=1990-01-01")
    assert response.status_code == 200
    assert response.json == {}
