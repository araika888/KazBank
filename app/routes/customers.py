
from flask import Blueprint, jsonify, request
from ..db import get_conn

bp = Blueprint("customers", __name__)


@bp.route("/customers", methods=["GET"])
def list_customers():
    city = request.args.get("city")

    if city:
        sql = """
            SELECT customer_id, full_name, city
            FROM customers
            WHERE city = %s
            ORDER BY customer_id
        """
        args = (city,)
    else:
        sql = """
            SELECT customer_id, full_name, city
            FROM customers
            ORDER BY customer_id
        """
        args = ()

    with get_conn() as conn:
        rows = conn.execute(sql, args).fetchall()

    return jsonify([
        {"id": r[0], "name": r[1], "city": r[2]}
        for r in rows
    ]), 200


@bp.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json(force=True)

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO customers (full_name, city, email)
            VALUES (%s, %s, %s)
            RETURNING customer_id
            """,
            (
                data.get("full_name"),
                data.get("city"),
                data.get("email")
            )
        )

        customer_id = cur.fetchone()[0]
        conn.commit()

    return jsonify({"customer_id": customer_id}), 201
