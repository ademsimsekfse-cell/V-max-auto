"""Tests for Vehicle endpoints."""

import json


def _make_customer(client):
    return client.post(
        "/customers/api/customers",
        data=json.dumps({"name": "Müşteri", "phone": "0500"}),
        content_type="application/json",
    ).get_json()["id"]


def _make_vehicle(client, customer_id=None, plate="34TEST01"):
    if customer_id is None:
        customer_id = _make_customer(client)
    return client.post(
        "/vehicles/api/vehicles",
        data=json.dumps({"customer_id": customer_id, "plate": plate, "brand": "Toyota", "model": "Corolla", "year": 2020}),
        content_type="application/json",
    )


class TestVehicleAPI:
    def test_list_empty(self, client):
        assert client.get("/vehicles/api/vehicles").get_json() == []

    def test_create_success(self, client):
        resp = _make_vehicle(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["plate"] == "34TEST01"
        assert data["brand"] == "Toyota"

    def test_plate_uppercased(self, client):
        cid = _make_customer(client)
        resp = client.post(
            "/vehicles/api/vehicles",
            data=json.dumps({"customer_id": cid, "plate": "34abc01", "brand": "BMW", "model": "3 Series"}),
            content_type="application/json",
        )
        assert resp.get_json()["plate"] == "34ABC01"

    def test_create_missing_fields(self, client):
        resp = client.post(
            "/vehicles/api/vehicles",
            data=json.dumps({"plate": "34X01"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_get_vehicle(self, client):
        _make_vehicle(client)
        resp = client.get("/vehicles/api/vehicles/1")
        assert resp.status_code == 200

    def test_update_vehicle(self, client):
        _make_vehicle(client)
        resp = client.put(
            "/vehicles/api/vehicles/1",
            data=json.dumps({"mileage": 75000}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["mileage"] == 75000

    def test_delete_vehicle(self, client):
        _make_vehicle(client)
        resp = client.delete("/vehicles/api/vehicles/1")
        assert resp.status_code == 200
        assert client.get("/vehicles/api/vehicles/1").status_code == 404
