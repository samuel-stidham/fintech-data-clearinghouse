from app.notifications import notify_external_services
from flask import Blueprint, jsonify, request
from sqlalchemy import select, text
from datetime import datetime
from . import db
from .models import Trade, ComplianceAlert

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


@bp.route("/blotter")
def get_blotter():
    """
    Endpoint A: GET blotter?date=<query date>
    Returns the data from the reports in a simplified format for the given date.
    """
    date_str = request.args.get("date")

    if not date_str:
        return jsonify({"error": "Missing required parameter: date"}), 400

    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        stmt = select(Trade).where(Trade.trade_date == query_date)
        results = db.session.execute(stmt).scalars().all()

        data = []
        for trade in results:
            data.append(
                {
                    "id": trade.id,
                    "ticker": trade.ticker,
                    "account": trade.account,
                    "quantity": trade.quantity,
                    "price": float(trade.price),
                    "total_value": float(trade.price) * abs(trade.quantity),
                }
            )

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/positions")
def get_positions():
    """
    Endpoint B: GET positions?date=<query date>
    Returns the percentage of funds by ticker for each account for the given date.
    """
    date_str = request.args.get("date")

    if not date_str:
        return jsonify({"error": "Missing required parameter: date"}), 400

    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        stmt = select(Trade).where(Trade.trade_date == query_date)
        trades = db.session.execute(stmt).scalars().all()

        account_totals = {}
        account_holdings = {}

        for t in trades:
            val = float(t.price) * abs(t.quantity)

            if t.account not in account_totals:
                account_totals[t.account] = 0.0
                account_holdings[t.account] = {}

            account_totals[t.account] += val

            current_ticker_val = account_holdings[t.account].get(t.ticker, 0.0)
            account_holdings[t.account][t.ticker] = current_ticker_val + val

        response_data = {}

        for acc_id, total_val in account_totals.items():
            response_data[acc_id] = {}
            holdings = account_holdings[acc_id]

            for ticker, ticker_val in holdings.items():
                if total_val > 0:
                    pct = (ticker_val / total_val) * 100
                    response_data[acc_id][ticker] = f"{pct:.1f}%"
                else:
                    response_data[acc_id][ticker] = "0.0%"

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/alarms")
def get_alarms():
    """
    Endpoint C: GET alarms?date=<query date>
    Returns true (and details) for any account that has over 20% of any ticker.
    """
    date_str = request.args.get("date")

    if not date_str:
        return jsonify({"error": "Missing required parameter: date"}), 400

    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        stmt = (
            select(ComplianceAlert, Trade)
            .join(Trade, ComplianceAlert.trade_id == Trade.id)
            .where(Trade.trade_date == query_date)
        )
        results = db.session.execute(stmt).all()

        alerts = []
        for alert, trade in results:
            alert_obj = {
                "account": trade.account,
                "ticker": trade.ticker,
                "rule": alert.rule_name,
                "description": alert.description,
                "triggered": True,
            }
            alerts.append(alert_obj)

            # Dummy function to represent external notification
            # In real implementation, this would send to an external system
            #
            notify_external_services(alert_obj)

        return jsonify(alerts), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
