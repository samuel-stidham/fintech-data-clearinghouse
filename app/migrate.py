import time
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from . import db, create_app, models


def wait_for_db(app):
    """Retries the DB connection until it is ready."""
    with app.app_context():
        retries = 0
        while retries < 30:
            try:
                db.session.execute(text("SELECT 1"))
                print("[Migration] Database is ready!")
                return True
            except OperationalError:
                retries += 1
                print(f"[Migration] Waiting for Database... ({retries}/30)")
                time.sleep(2)

        print("[Migration] Could not connect to Database after 60s.")
        return False


def run_migrations():
    """Creates all tables defined in SQLAlchemy models."""
    app = create_app()

    if wait_for_db(app):
        with app.app_context():
            print("[Migration] Creating tables...")
            try:
                db.create_all()
                print("[Migration] Tables created successfully.")
            except Exception as e:
                print(f"[Migration] Error creating tables: {e}")


if __name__ == "__main__":
    run_migrations()
