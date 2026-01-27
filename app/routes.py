from flask import Blueprint, jsonify
from sqlalchemy import text
from . import db

bp = Blueprint("main", __name__)


@bp.route("/health", methods=["GET"])
def health():
    """Operational Endpoint: Checks app status and DB connectivity."""
    try:
        db.session.execute(text("SELECT 1"))
        return (
            jsonify(
                {
                    "status": "OK",
                    "database": "connected",
                    "service": "clearinghouse-api",
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 500
