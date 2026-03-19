"""Tests for Invoice and Expense endpoints."""

import json


def _full_setup(client):
    """Create customer → vehicle → service order. Return order id."""
    cid = client.post(
        "/customers/api/customers",
        data=json.dumps({"name": "Müşteri", "phone": "0500"}),
        content_type="application/json",
    ).get_json()["id"]
    vid = client.post(
        "/vehicles/api/vehicles",
        data=json.dumps({"customer_id": cid, "plate": "07INV01", "brand": "Audi", "model": "A4"}),
        content_type="application/json",
    ).get_json()["id"]
    oid = client.post(
        "/service-orders/api/service-orders",
        data=json.dumps({"vehicle_id": vid, "description": "Fren bakımı", "labor_cost": 200, "parts_cost": 300}),
        content_type="application/json",
    ).get_json()["id"]
    return oid


class TestInvoiceAPI:
    def test_create_invoice(self, client):
        oid = _full_setup(client)
        resp = client.post(
            "/invoices/api/invoices",
            data=json.dumps({"service_order_id": oid, "amount": 500.0}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["amount"] == 500.0
        assert data["status"] == "Bekliyor"

    def test_create_missing_fields(self, client):
        resp = client.post(
            "/invoices/api/invoices",
            data=json.dumps({"service_order_id": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_mark_paid(self, client):
        oid = _full_setup(client)
        client.post(
            "/invoices/api/invoices",
            data=json.dumps({"service_order_id": oid, "amount": 500.0}),
            content_type="application/json",
        )
        resp = client.post("/invoices/api/invoices/1/pay")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "Ödendi"
        assert resp.get_json()["paid_at"] is not None

    def test_delete_invoice(self, client):
        oid = _full_setup(client)
        client.post(
            "/invoices/api/invoices",
            data=json.dumps({"service_order_id": oid, "amount": 500.0}),
            content_type="application/json",
        )
        resp = client.delete("/invoices/api/invoices/1")
        assert resp.status_code == 200
        assert client.get("/invoices/api/invoices/1").status_code == 404


class TestExpenseAPI:
    def test_create_expense(self, client):
        resp = client.post(
            "/expenses/api/expenses",
            data=json.dumps({"category": "Kira", "description": "Mart kirası", "amount": 5000, "date": "2025-03-01"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["category"] == "Kira"
        assert data["amount"] == 5000.0

    def test_create_missing_fields(self, client):
        resp = client.post(
            "/expenses/api/expenses",
            data=json.dumps({"category": "Kira"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_update_expense(self, client):
        client.post(
            "/expenses/api/expenses",
            data=json.dumps({"category": "Kira", "description": "Test", "amount": 1000, "date": "2025-01-01"}),
            content_type="application/json",
        )
        resp = client.put(
            "/expenses/api/expenses/1",
            data=json.dumps({"amount": 1500}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["amount"] == 1500.0

    def test_delete_expense(self, client):
        client.post(
            "/expenses/api/expenses",
            data=json.dumps({"category": "Yakıt", "description": "Akaryakıt", "amount": 200, "date": "2025-02-01"}),
            content_type="application/json",
        )
        resp = client.delete("/expenses/api/expenses/1")
        assert resp.status_code == 200
        assert client.get("/expenses/api/expenses/1").status_code == 404


class TestDashboard:
    def test_dashboard_loads(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.data.decode()
        assert "Dashboard" in body
        assert "V-max" in body

    def test_dashboard_stats(self, client):
        """Dashboard should reflect created data."""
        oid = _full_setup(client)
        client.post(
            "/invoices/api/invoices",
            data=json.dumps({"service_order_id": oid, "amount": 500.0}),
            content_type="application/json",
        )
        client.post("/invoices/api/invoices/1/pay")

        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.data.decode()
        assert "500" in body
