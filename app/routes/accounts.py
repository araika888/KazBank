from flask import Blueprint, jsonify, request
from ..db import get_conn

bp = Blueprint("accounts", __name__)

# GET /accounts?customer_id=1
@bp.route("/accounts")
def list_accounts():
    customer_id = request.args.get("customer_id", type=int)
    if customer_id is None:
        return jsonify({"error": "customer_id query parameter is required"}), 400

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT account_id, account_number, balance FROM accounts "
            "WHERE customer_id = %s ORDER BY account_id",
            (customer_id,),
        ).fetchall()

    return jsonify([
        {"account_id": r[0], "account_number": r[1], "balance": float(r[2])}
        for r in rows
    ])