from flask import Flask

def create_app():
    app = Flask(__name__)

    from .routes.customers import bp as customers_bp
    from .routes.accounts import bp as accounts_bp
    from .routes.transactions import bp as transactions_bp

    app.register_blueprint(customers_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)

    return app