import pytest
from app import create_app, db
from app.models import Trade


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def seed_data(app):
    """Pre-populates the DB with some trades for testing blotter."""
    with app.app_context():
        t1 = Trade(
            trade_date="2025-01-15",
            account="ACC001",
            ticker="AAPL",
            quantity=100,
            price=150.00,
        )
        t2 = Trade(
            trade_date="2025-01-15",
            account="ACC002",
            ticker="GOOG",
            quantity=50,
            price=2000.00,
        )
        t3 = Trade(
            trade_date="2025-01-16",
            account="ACC001",
            ticker="MSFT",
            quantity=10,
            price=300.00,
        )

        db.session.add_all([t1, t2, t3])
        db.session.commit()
