
from flask import Flask, jsonify
import psycopg
from psycopg import errors as pg_errors
from .db import pool


def create_app():
    app = Flask(__name__)

    from .routes.customers import bp as customers_bp
    from .routes.accounts import bp as accounts_bp
    from .routes.transactions import bp as transactions_bp

    app.register_blueprint(customers_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)

    # Error handlers

    @app.errorhandler(pg_errors.UniqueViolation)
    def handle_unique_violation(e):
        return jsonify({
            "error": "Email already registered"
        }), 409

    @app.errorhandler(pg_errors.NotNullViolation)
    def handle_not_null(e):
        return jsonify({
            "error": f"Missing required field: {e.diag.column_name}"
        }), 400

    @app.errorhandler(pg_errors.ForeignKeyViolation)
    def handle_foreign_key(e):
        return jsonify({
            "error": "Related record does not exist"
        }), 400

    @app.errorhandler(psycopg.OperationalError)
    def handle_operational(e):
        return jsonify({
            "error": "Database unavailable"
        }), 503

    # Health check endpoint

    @app.route("/health", methods=["GET"])
    def health():
        try:
            pool.check()

            return jsonify({
                "status": "ok",
                "pool_stats": pool.get_stats()
            }), 200

        except Exception as e:
            return jsonify({
                "status": "error",
                "detail": str(e)
            }), 503

    return app
