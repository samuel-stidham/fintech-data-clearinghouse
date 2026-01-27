from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize SQLAlchemy (so other files can import it)
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///local.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from .routes import bp as main_bp

    app.register_blueprint(main_bp)

    if (
        os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        or os.environ.get("FLASK_ENV") == "production"
    ):
        from .ingest import SftpIngestionService

        ingestor = SftpIngestionService(app)
        ingestor.start_background_loop()

    return app
