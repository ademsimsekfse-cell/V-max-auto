"""V-max Auto Service Automation & Accounting Application."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    if test_config is None:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vmax.db"
        app.config["SECRET_KEY"] = "vmax-secret-key-change-in-production"
    else:
        app.config.update(test_config)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.models import Customer, Vehicle, ServiceOrder, Invoice, Expense  # noqa: F401

    from app.routes import customers, vehicles, service_orders, invoices, expenses, main

    app.register_blueprint(main.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(vehicles.bp)
    app.register_blueprint(service_orders.bp)
    app.register_blueprint(invoices.bp)
    app.register_blueprint(expenses.bp)

    with app.app_context():
        db.create_all()

    return app
