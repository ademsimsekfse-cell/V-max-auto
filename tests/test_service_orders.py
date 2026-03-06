"""Tests for ServiceOrder endpoints."""

import json


def _setup(client):
    cid = client.post(
        "/customers/api/customers",
        data=json.dumps({"name": "Müşteri", "phone": "0500"}),
        content_type="application/json",
    ).get_json()["id"]
    vid = client.post(
        "/vehicles/api/vehicles",
        data=json.dumps({"customer_id": cid, "plate": "06TEST01", "brand": "Ford", "model": "Focus"}),
        content_type="application/json",
    ).get_json()["id"]
    return vid


def _make_order(client, vehicle_id=None):
    if vehicle_id is None:
        vehicle_id = _setup(client)
    return client.post(
        "/service-orders/api/service-orders",
        data=json.dumps({
            "vehicle_id": vehicle_id,
            "description": "Motor yağı değişimi",
            "labor_cost": 150.0,
            "parts_cost": 200.0,
        }),
        content_type="application/json",
    )


class TestServiceOrderAPI:
    def test_create_order(self, client):
        resp = _make_order(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["description"] == "Motor yağı değişimi"
        assert data["total_cost"] == 350.0
        assert data["status"] == "Açık"

    def test_total_cost_computed(self, client):
        vid = _setup(client)
        resp = client.post(
            "/service-orders/api/service-orders",
            data=json.dumps({"vehicle_id": vid, "description": "Test", "labor_cost": 100, "parts_cost": 50}),
            content_type="application/json",
        )
        assert resp.get_json()["total_cost"] == 150.0

    def test_create_missing_fields(self, client):
        resp = client.post(
            "/service-orders/api/service-orders",
            data=json.dumps({"vehicle_id": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_update_status(self, client):
        _make_order(client)
        resp = client.put(
            "/service-orders/api/service-orders/1",
            data=json.dumps({"status": "Tamamlandı"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "Tamamlandı"

    def test_delete_order(self, client):
        _make_order(client)
        resp = client.delete("/service-orders/api/service-orders/1")
        assert resp.status_code == 200
        assert client.get("/service-orders/api/service-orders/1").status_code == 404

    def test_list_orders(self, client):
        vid = _setup(client)
        _make_order(client, vid)
        _make_order(client, vid)
        resp = client.get("/service-orders/api/service-orders")
        assert len(resp.get_json()) == 2
