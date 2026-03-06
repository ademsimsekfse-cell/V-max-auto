"""Database models for V-max Auto Service."""

from datetime import datetime, timezone

from app import db


class Customer(db.Model):
    """Müşteri (Customer) model."""

    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    vehicles = db.relationship("Vehicle", backref="customer", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Vehicle(db.Model):
    """Araç (Vehicle) model."""

    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    plate = db.Column(db.String(20), nullable=False, unique=True)
    brand = db.Column(db.String(60), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    mileage = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    service_orders = db.relationship("ServiceOrder", backref="vehicle", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "plate": self.plate,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "mileage": self.mileage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ServiceOrder(db.Model):
    """Servis Emri (Service Order) model."""

    __tablename__ = "service_orders"

    STATUS_OPEN = "Açık"
    STATUS_IN_PROGRESS = "Devam Ediyor"
    STATUS_DONE = "Tamamlandı"
    STATUS_CANCELLED = "İptal"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default=STATUS_OPEN)
    labor_cost = db.Column(db.Float, nullable=False, default=0.0)
    parts_cost = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    invoice = db.relationship("Invoice", backref="service_order", uselist=False, cascade="all, delete-orphan")

    @property
    def total_cost(self):
        return self.labor_cost + self.parts_cost

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "description": self.description,
            "status": self.status,
            "labor_cost": self.labor_cost,
            "parts_cost": self.parts_cost,
            "total_cost": self.total_cost,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Invoice(db.Model):
    """Fatura (Invoice) model."""

    __tablename__ = "invoices"

    STATUS_PENDING = "Bekliyor"
    STATUS_PAID = "Ödendi"
    STATUS_CANCELLED = "İptal"

    id = db.Column(db.Integer, primary_key=True)
    service_order_id = db.Column(db.Integer, db.ForeignKey("service_orders.id"), nullable=False, unique=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "service_order_id": self.service_order_id,
            "amount": self.amount,
            "status": self.status,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }


class Expense(db.Model):
    """Gider (Expense) model."""

    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "description": self.description,
            "amount": self.amount,
            "date": self.date.isoformat() if self.date else None,
        }
