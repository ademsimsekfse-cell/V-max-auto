"""Tests for data model integrity and relationships."""

import pytest

from app.models import Customer, Expense, Invoice, ServiceOrder, Vehicle


class TestModels:
    def test_customer_to_dict(self, db):
        c = Customer(name="Test", phone="0500")
        db.session.add(c)
        db.session.commit()
        d = c.to_dict()
        assert d["name"] == "Test"
        assert d["phone"] == "0500"
        assert "id" in d
        assert "created_at" in d

    def test_vehicle_belongs_to_customer(self, db):
        c = Customer(name="Owner", phone="111")
        db.session.add(c)
        db.session.flush()
        v = Vehicle(customer_id=c.id, plate="34X01", brand="VW", model="Golf")
        db.session.add(v)
        db.session.commit()
        assert v.customer.name == "Owner"

    def test_cascade_delete_customer_removes_vehicle(self, db):
        c = Customer(name="Del Test", phone="222")
        db.session.add(c)
        db.session.flush()
        v = Vehicle(customer_id=c.id, plate="06DEL", brand="Fiat", model="Egea")
        db.session.add(v)
        db.session.commit()
        db.session.delete(c)
        db.session.commit()
        assert db.session.get(Vehicle, v.id) is None

    def test_service_order_total_cost(self, db):
        c = Customer(name="C", phone="333")
        db.session.add(c)
        db.session.flush()
        v = Vehicle(customer_id=c.id, plate="35TC01", brand="Renault", model="Clio")
        db.session.add(v)
        db.session.flush()
        o = ServiceOrder(vehicle_id=v.id, description="Test", labor_cost=100.0, parts_cost=250.0)
        db.session.add(o)
        db.session.commit()
        assert o.total_cost == 350.0

    def test_service_order_default_status(self, db):
        c = Customer(name="D", phone="444")
        db.session.add(c)
        db.session.flush()
        v = Vehicle(customer_id=c.id, plate="35TD01", brand="Honda", model="Civic")
        db.session.add(v)
        db.session.flush()
        o = ServiceOrder(vehicle_id=v.id, description="Default status test")
        db.session.add(o)
        db.session.commit()
        assert o.status == ServiceOrder.STATUS_OPEN

    def test_expense_to_dict(self, db):
        from datetime import date
        e = Expense(category="Yakıt", description="Benzin", amount=200.0, date=date(2025, 3, 1))
        db.session.add(e)
        db.session.commit()
        d = e.to_dict()
        assert d["category"] == "Yakıt"
        assert d["amount"] == 200.0
        assert d["date"] == "2025-03-01"
