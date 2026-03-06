"""Customer routes (REST API + HTML views)."""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app import db
from app.models import Customer

bp = Blueprint("customers", __name__, url_prefix="/customers")


@bp.route("/")
def list_customers():
    customers = db.session.execute(db.select(Customer).order_by(Customer.name)).scalars().all()
    return render_template("customers/list.html", customers=customers)


@bp.route("/new", methods=["GET", "POST"])
def create_customer():
    if request.method == "POST":
        data = request.form
        customer = Customer(
            name=data["name"],
            phone=data["phone"],
            email=data.get("email", ""),
            address=data.get("address", ""),
        )
        db.session.add(customer)
        db.session.commit()
        return redirect(url_for("customers.list_customers"))
    return render_template("customers/form.html", customer=None)


@bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
def edit_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    if request.method == "POST":
        data = request.form
        customer.name = data["name"]
        customer.phone = data["phone"]
        customer.email = data.get("email", "")
        customer.address = data.get("address", "")
        db.session.commit()
        return redirect(url_for("customers.list_customers"))
    return render_template("customers/form.html", customer=customer)


@bp.route("/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for("customers.list_customers"))


# --- JSON API ---

@bp.route("/api/customers", methods=["GET"])
def api_list():
    customers = db.session.execute(db.select(Customer).order_by(Customer.name)).scalars().all()
    return jsonify([c.to_dict() for c in customers])


@bp.route("/api/customers", methods=["POST"])
def api_create():
    data = request.get_json(force=True)
    if not data or not data.get("name") or not data.get("phone"):
        return jsonify({"error": "name ve phone alanları zorunludur"}), 400
    customer = Customer(
        name=data["name"],
        phone=data["phone"],
        email=data.get("email", ""),
        address=data.get("address", ""),
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify(customer.to_dict()), 201


@bp.route("/api/customers/<int:customer_id>", methods=["GET"])
def api_get(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    return jsonify(customer.to_dict())


@bp.route("/api/customers/<int:customer_id>", methods=["PUT"])
def api_update(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "JSON gövdesi gereklidir"}), 400
    customer.name = data.get("name", customer.name)
    customer.phone = data.get("phone", customer.phone)
    customer.email = data.get("email", customer.email)
    customer.address = data.get("address", customer.address)
    db.session.commit()
    return jsonify(customer.to_dict())


@bp.route("/api/customers/<int:customer_id>", methods=["DELETE"])
def api_delete(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Müşteri silindi"}), 200
