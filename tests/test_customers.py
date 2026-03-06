"""Tests for Customer endpoints."""

import json

import pytest

from app.models import Customer


def _create_customer(client, name="Ali Veli", phone="05001234567"):
    return client.post(
        "/customers/api/customers",
        data=json.dumps({"name": name, "phone": phone}),
        content_type="application/json",
    )


class TestCustomerAPI:
    def test_list_empty(self, client):
        resp = client.get("/customers/api/customers")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_create_success(self, client):
        resp = _create_customer(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Ali Veli"
        assert data["phone"] == "05001234567"
        assert data["id"] == 1

    def test_create_missing_fields(self, client):
        resp = client.post(
            "/customers/api/customers",
            data=json.dumps({"name": "Sadece İsim"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_get_customer(self, client):
        _create_customer(client)
        resp = client.get("/customers/api/customers/1")
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Ali Veli"

    def test_get_nonexistent(self, client):
        resp = client.get("/customers/api/customers/999")
        assert resp.status_code == 404

    def test_update_customer(self, client):
        _create_customer(client)
        resp = client.put(
            "/customers/api/customers/1",
            data=json.dumps({"name": "Güncellendi"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Güncellendi"

    def test_delete_customer(self, client):
        _create_customer(client)
        resp = client.delete("/customers/api/customers/1")
        assert resp.status_code == 200
        # confirm gone
        assert client.get("/customers/api/customers/1").status_code == 404

    def test_list_after_create(self, client):
        _create_customer(client, name="A", phone="111")
        _create_customer(client, name="B", phone="222")
        resp = client.get("/customers/api/customers")
        assert len(resp.get_json()) == 2


class TestCustomerHTMLViews:
    def test_list_page(self, client):
        resp = client.get("/customers/")
        assert resp.status_code == 200
        assert "Müşteriler" in resp.data.decode()

    def test_new_form_page(self, client):
        resp = client.get("/customers/new")
        assert resp.status_code == 200

    def test_create_via_form(self, client):
        resp = client.post(
            "/customers/new",
            data={"name": "Form Müşteri", "phone": "05550000001"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert "Form Müşteri" in resp.data.decode()
