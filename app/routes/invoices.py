"""Invoice routes."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app import db
from app.models import Invoice, ServiceOrder

bp = Blueprint("invoices", __name__, url_prefix="/invoices")


@bp.route("/")
def list_invoices():
    invoices = db.session.execute(
        db.select(Invoice).order_by(Invoice.issued_at.desc())
    ).scalars().all()
    return render_template("invoices/list.html", invoices=invoices)


@bp.route("/new", methods=["GET", "POST"])
def create_invoice():
    completed_orders = db.session.execute(
        db.select(ServiceOrder).where(ServiceOrder.invoice == None)  # noqa: E711
    ).scalars().all()
    if request.method == "POST":
        data = request.form
        order_id = int(data["service_order_id"])
        order = db.get_or_404(ServiceOrder, order_id)
        invoice = Invoice(
            service_order_id=order_id,
            amount=float(data.get("amount") or order.total_cost),
            status=Invoice.STATUS_PENDING,
        )
        db.session.add(invoice)
        db.session.commit()
        return redirect(url_for("invoices.list_invoices"))
    return render_template("invoices/form.html", invoice=None, orders=completed_orders)


@bp.route("/<int:invoice_id>/pay", methods=["POST"])
def mark_paid(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    invoice.status = Invoice.STATUS_PAID
    invoice.paid_at = datetime.now(timezone.utc)
    db.session.commit()
    return redirect(url_for("invoices.list_invoices"))


@bp.route("/<int:invoice_id>/delete", methods=["POST"])
def delete_invoice(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    return redirect(url_for("invoices.list_invoices"))


# --- JSON API ---

@bp.route("/api/invoices", methods=["GET"])
def api_list():
    invoices = db.session.execute(
        db.select(Invoice).order_by(Invoice.issued_at.desc())
    ).scalars().all()
    return jsonify([i.to_dict() for i in invoices])


@bp.route("/api/invoices", methods=["POST"])
def api_create():
    data = request.get_json(force=True)
    if not data or not data.get("service_order_id") or not data.get("amount"):
        return jsonify({"error": "service_order_id ve amount alanları zorunludur"}), 400
    invoice = Invoice(
        service_order_id=data["service_order_id"],
        amount=float(data["amount"]),
        status=data.get("status", Invoice.STATUS_PENDING),
    )
    db.session.add(invoice)
    db.session.commit()
    return jsonify(invoice.to_dict()), 201


@bp.route("/api/invoices/<int:invoice_id>", methods=["GET"])
def api_get(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    return jsonify(invoice.to_dict())


@bp.route("/api/invoices/<int:invoice_id>/pay", methods=["POST"])
def api_pay(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    invoice.status = Invoice.STATUS_PAID
    invoice.paid_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(invoice.to_dict())


@bp.route("/api/invoices/<int:invoice_id>", methods=["DELETE"])
def api_delete(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    return jsonify({"message": "Fatura silindi"}), 200
