
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from psycopg import IsolationLevel
import psycopg
import time
from ..db import get_conn

bp = Blueprint("transactions", __name__)


# Retry wrapper
def with_retry(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fn()
        except psycopg.errors.SerializationFailure:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.05 * (attempt + 1))

    raise RuntimeError("Max retries exceeded")


# GET /transactions?account_id=n
@bp.route("/transactions", methods=["GET"])
def list_transactions():
    account_id = request.args.get("account_id")

    if not account_id:
        return jsonify({"error": "account_id is required"}), 400

    try:
        account_id = int(account_id)
    except ValueError:
        return jsonify({"error": "account_id must be an integer"}), 400

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT transaction_id, account_id, transaction_type, amount
            FROM transactions
            WHERE account_id = %s
            ORDER BY transaction_id DESC
            """,
            (account_id,),
        ).fetchall()

    return jsonify([
        {
            "transaction_id": row[0],
            "account_id": row[1],
            "type": row[2],
            "amount": float(row[3])
        }
        for row in rows
    ]), 200


# POST /transactions
@bp.route("/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json(force=True)

    account_id = data.get("account_id")
    tx_type = data.get("type")

    if tx_type not in ("debit", "credit"):
        return jsonify({"error": "type must be 'debit' or 'credit'"}), 400

    try:
        amount = Decimal(str(data.get("amount")))
    except (InvalidOperation, TypeError):
        return jsonify({"error": "amount must be a number"}), 400

    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    with get_conn() as conn:
        row = conn.execute(
            "SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE",
            (account_id,),
        ).fetchone()

        if row is None:
            return jsonify({"error": "account not found"}), 404

        balance = row[0]
        new_balance = balance - amount if tx_type == "debit" else balance + amount

        if new_balance < 0:
            return jsonify({"error": "insufficient funds"}), 400

        conn.execute(
            "UPDATE accounts SET balance = %s WHERE account_id = %s",
            (new_balance, account_id),
        )

        cur = conn.execute(
            """
            INSERT INTO transactions (account_id, transaction_type, amount)
            VALUES (%s, %s, %s)
            RETURNING transaction_id
            """,
            (account_id, tx_type, amount),
        )

        tx_id = cur.fetchone()[0]
        conn.commit()

    return jsonify({
        "transaction_id": tx_id,
        "new_balance": float(new_balance)
    }), 201


# Transfer operation
def perform_transfer(from_account, to_account, amount):
    with get_conn() as conn:
        conn.isolation_level = IsolationLevel.SERIALIZABLE

        first, second = sorted([from_account, to_account])

        conn.execute(
            "SELECT 1 FROM accounts WHERE account_id = %s FOR UPDATE",
            (first,),
        )

        conn.execute(
            "SELECT 1 FROM accounts WHERE account_id = %s FOR UPDATE",
            (second,),
        )

        rows = conn.execute(
            """
            SELECT account_id, balance
            FROM accounts
            WHERE account_id IN (%s, %s)
            """,
            (from_account, to_account),
        ).fetchall()

        accounts = {row[0]: row[1] for row in rows}

        if from_account not in accounts or to_account not in accounts:
            return {"error": "Account not found"}, 404

        if accounts[from_account] < amount:
            return {"error": "Insufficient funds"}, 400

        conn.execute("SAVEPOINT transfer_start")

        try:
            conn.execute(
                "UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                (amount, from_account),
            )

            conn.execute(
                "UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                (amount, to_account),
            )

            conn.execute(
                """
                INSERT INTO transactions
                    (account_id, transaction_type, amount)
                VALUES (%s, 'debit', %s), (%s, 'credit', %s)
                """,
                (from_account, amount, to_account, amount),
            )

            conn.execute("RELEASE SAVEPOINT transfer_start")
            conn.commit()

        except Exception:
            conn.execute("ROLLBACK TO SAVEPOINT transfer_start")
            conn.rollback()
            raise

    return {"message": "Transfer successful"}, 200


# POST /transfer
@bp.route("/transfer", methods=["POST"])
def transfer_money():
    data = request.get_json(force=True)

    from_account = data.get("from_account")
    to_account = data.get("to_account")

    try:
        amount = Decimal(str(data.get("amount")))
    except (InvalidOperation, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    if from_account == to_account:
        return jsonify({"error": "Accounts must be different"}), 400

    try:
        result, status = with_retry(
            lambda: perform_transfer(from_account, to_account, amount)
        )
        return jsonify(result), status

    except psycopg.errors.SerializationFailure:
        return jsonify({
            "error": "Transfer failed after 3 attempts. Please try again."
        }), 409
