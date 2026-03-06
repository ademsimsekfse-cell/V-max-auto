"""Vehicle routes."""

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app import db
from app.models import Customer, Vehicle

bp = Blueprint("vehicles", __name__, url_prefix="/vehicles")


@bp.route("/")
def list_vehicles():
    vehicles = db.session.execute(db.select(Vehicle).order_by(Vehicle.plate)).scalars().all()
    return render_template("vehicles/list.html", vehicles=vehicles)


@bp.route("/new", methods=["GET", "POST"])
def create_vehicle():
    customers = db.session.execute(db.select(Customer).order_by(Customer.name)).scalars().all()
    if request.method == "POST":
        data = request.form
        vehicle = Vehicle(
            customer_id=int(data["customer_id"]),
            plate=data["plate"].upper().strip(),
            brand=data["brand"],
            model=data["model"],
            year=int(data["year"]) if data.get("year") else None,
            mileage=int(data["mileage"]) if data.get("mileage") else None,
        )
        db.session.add(vehicle)
        db.session.commit()
        return redirect(url_for("vehicles.list_vehicles"))
    return render_template("vehicles/form.html", vehicle=None, customers=customers)


@bp.route("/<int:vehicle_id>/edit", methods=["GET", "POST"])
def edit_vehicle(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    customers = db.session.execute(db.select(Customer).order_by(Customer.name)).scalars().all()
    if request.method == "POST":
        data = request.form
        vehicle.customer_id = int(data["customer_id"])
        vehicle.plate = data["plate"].upper().strip()
        vehicle.brand = data["brand"]
        vehicle.model = data["model"]
        vehicle.year = int(data["year"]) if data.get("year") else None
        vehicle.mileage = int(data["mileage"]) if data.get("mileage") else None
        db.session.commit()
        return redirect(url_for("vehicles.list_vehicles"))
    return render_template("vehicles/form.html", vehicle=vehicle, customers=customers)


@bp.route("/<int:vehicle_id>/delete", methods=["POST"])
def delete_vehicle(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return redirect(url_for("vehicles.list_vehicles"))


# --- JSON API ---

@bp.route("/api/vehicles", methods=["GET"])
def api_list():
    vehicles = db.session.execute(db.select(Vehicle).order_by(Vehicle.plate)).scalars().all()
    return jsonify([v.to_dict() for v in vehicles])


@bp.route("/api/vehicles", methods=["POST"])
def api_create():
    data = request.get_json(force=True)
    required = ["customer_id", "plate", "brand", "model"]
    if not data or any(not data.get(f) for f in required):
        return jsonify({"error": "customer_id, plate, brand ve model alanları zorunludur"}), 400
    vehicle = Vehicle(
        customer_id=data["customer_id"],
        plate=data["plate"].upper().strip(),
        brand=data["brand"],
        model=data["model"],
        year=data.get("year"),
        mileage=data.get("mileage"),
    )
    db.session.add(vehicle)
    db.session.commit()
    return jsonify(vehicle.to_dict()), 201


@bp.route("/api/vehicles/<int:vehicle_id>", methods=["GET"])
def api_get(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    return jsonify(vehicle.to_dict())


@bp.route("/api/vehicles/<int:vehicle_id>", methods=["PUT"])
def api_update(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "JSON gövdesi gereklidir"}), 400
    if "plate" in data:
        vehicle.plate = data["plate"].upper().strip()
    vehicle.brand = data.get("brand", vehicle.brand)
    vehicle.model = data.get("model", vehicle.model)
    vehicle.year = data.get("year", vehicle.year)
    vehicle.mileage = data.get("mileage", vehicle.mileage)
    db.session.commit()
    return jsonify(vehicle.to_dict())


@bp.route("/api/vehicles/<int:vehicle_id>", methods=["DELETE"])
def api_delete(vehicle_id):
    vehicle = db.get_or_404(Vehicle, vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({"message": "Araç silindi"}), 200
