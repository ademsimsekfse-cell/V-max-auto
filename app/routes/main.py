"""Main / dashboard routes."""

from flask import Blueprint, render_template
from sqlalchemy import func

from app import db
from app.models import Customer, Expense, Invoice, ServiceOrder, Vehicle

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    total_customers = db.session.execute(db.select(func.count(Customer.id))).scalar()
    total_vehicles = db.session.execute(db.select(func.count(Vehicle.id))).scalar()
    open_orders = db.session.execute(
        db.select(func.count(ServiceOrder.id)).where(ServiceOrder.status == ServiceOrder.STATUS_OPEN)
    ).scalar()
    pending_invoices = db.session.execute(
        db.select(func.count(Invoice.id)).where(Invoice.status == Invoice.STATUS_PENDING)
    ).scalar()
    total_income = db.session.execute(
        db.select(func.coalesce(func.sum(Invoice.amount), 0)).where(Invoice.status == Invoice.STATUS_PAID)
    ).scalar()
    total_expenses = db.session.execute(
        db.select(func.coalesce(func.sum(Expense.amount), 0))
    ).scalar()

    return render_template(
        "index.html",
        total_customers=total_customers,
        total_vehicles=total_vehicles,
        open_orders=open_orders,
        pending_invoices=pending_invoices,
        total_income=float(total_income),
        total_expenses=float(total_expenses),
        net_profit=float(total_income) - float(total_expenses),
    )
