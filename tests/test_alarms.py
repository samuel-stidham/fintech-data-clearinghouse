from datetime import date
from app import db
from app.models import Trade, ComplianceAlert


def test_alarms_none(client, app):
    """Test a date with trades but NO alerts."""
    with app.app_context():
        t1 = Trade(
            trade_date=date(2025, 3, 1),
            account="SAFE_ACC",
            ticker="AAPL",
            quantity=10,
            price=10.00,
        )
        db.session.add(t1)
        db.session.commit()

    response = client.get("/alarms?date=2025-03-01")
    assert response.status_code == 200
    assert response.json == []


def test_alarms_found(client, app):
    """Test retrieving alerts for a specific date."""
    with app.app_context():
        t1 = Trade(
            trade_date=date(2025, 3, 2),
            account="RISKY_ACC",
            ticker="MEME",
            quantity=1000,
            price=10.00,
        )
        db.session.add(t1)
        db.session.flush()

        alert = ComplianceAlert(
            trade_id=t1.id,
            rule_name="Basket Concentration (>20%)",
            severity="WARNING",
            description="Ticker MEME is 100% of basket",
        )
        db.session.add(alert)
        db.session.commit()

    response = client.get("/alarms?date=2025-03-02")
    assert response.status_code == 200

    data = response.json
    assert len(data) == 1
    assert data[0]["account"] == "RISKY_ACC"
    assert data[0]["ticker"] == "MEME"
    assert data[0]["triggered"] is True
