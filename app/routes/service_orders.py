"""Service Order routes."""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app import db
from app.models import ServiceOrder, Vehicle

bp = Blueprint("service_orders", __name__, url_prefix="/service-orders")

VALID_STATUSES = [
    ServiceOrder.STATUS_OPEN,
    ServiceOrder.STATUS_IN_PROGRESS,
    ServiceOrder.STATUS_DONE,
    ServiceOrder.STATUS_CANCELLED,
]


@bp.route("/")
def list_orders():
    orders = db.session.execute(
        db.select(ServiceOrder).order_by(ServiceOrder.created_at.desc())
    ).scalars().all()
    return render_template("service_orders/list.html", orders=orders)


@bp.route("/new", methods=["GET", "POST"])
def create_order():
    vehicles = db.session.execute(db.select(Vehicle).order_by(Vehicle.plate)).scalars().all()
    if request.method == "POST":
        data = request.form
        order = ServiceOrder(
            vehicle_id=int(data["vehicle_id"]),
            description=data["description"],
            status=data.get("status", ServiceOrder.STATUS_OPEN),
            labor_cost=float(data.get("labor_cost") or 0),
            parts_cost=float(data.get("parts_cost") or 0),
        )
        db.session.add(order)
        db.session.commit()
        return redirect(url_for("service_orders.list_orders"))
    return render_template("service_orders/form.html", order=None, vehicles=vehicles, statuses=VALID_STATUSES)


@bp.route("/<int:order_id>/edit", methods=["GET", "POST"])
def edit_order(order_id):
    order = db.get_or_404(ServiceOrder, order_id)
    vehicles = db.session.execute(db.select(Vehicle).order_by(Vehicle.plate)).scalars().all()
    if request.method == "POST":
        data = request.form
        order.vehicle_id = int(data["vehicle_id"])
        order.description = data["description"]
        order.status = data.get("status", order.status)
        order.labor_cost = float(data.get("labor_cost") or 0)
        order.parts_cost = float(data.get("parts_cost") or 0)
        db.session.commit()
        return redirect(url_for("service_orders.list_orders"))
    return render_template("service_orders/form.html", order=order, vehicles=vehicles, statuses=VALID_STATUSES)


@bp.route("/<int:order_id>/delete", methods=["POST"])
def delete_order(order_id):
    order = db.get_or_404(ServiceOrder, order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for("service_orders.list_orders"))


# --- JSON API ---

@bp.route("/api/service-orders", methods=["GET"])
def api_list():
    orders = db.session.execute(
        db.select(ServiceOrder).order_by(ServiceOrder.created_at.desc())
    ).scalars().all()
    return jsonify([o.to_dict() for o in orders])


@bp.route("/api/service-orders", methods=["POST"])
def api_create():
    data = request.get_json(force=True)
    if not data or not data.get("vehicle_id") or not data.get("description"):
        return jsonify({"error": "vehicle_id ve description alanları zorunludur"}), 400
    order = ServiceOrder(
        vehicle_id=data["vehicle_id"],
        description=data["description"],
        status=data.get("status", ServiceOrder.STATUS_OPEN),
        labor_cost=float(data.get("labor_cost", 0)),
        parts_cost=float(data.get("parts_cost", 0)),
    )
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201


@bp.route("/api/service-orders/<int:order_id>", methods=["GET"])
def api_get(order_id):
    order = db.get_or_404(ServiceOrder, order_id)
    return jsonify(order.to_dict())


@bp.route("/api/service-orders/<int:order_id>", methods=["PUT"])
def api_update(order_id):
    order = db.get_or_404(ServiceOrder, order_id)
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "JSON gövdesi gereklidir"}), 400
    order.description = data.get("description", order.description)
    order.status = data.get("status", order.status)
    order.labor_cost = float(data.get("labor_cost", order.labor_cost))
    order.parts_cost = float(data.get("parts_cost", order.parts_cost))
    db.session.commit()
    return jsonify(order.to_dict())


@bp.route("/api/service-orders/<int:order_id>", methods=["DELETE"])
def api_delete(order_id):
    order = db.get_or_404(ServiceOrder, order_id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Servis emri silindi"}), 200
