"""Shared test fixtures."""

import pytest

from app import create_app, db as _db


@pytest.fixture()
def app():
    """Create an application instance configured for testing."""
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    }
    app = create_app(test_config)

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Return a test client for the app."""
    return app.test_client()


@pytest.fixture()
def db(app):
    """Return a database session scoped to the test."""
    with app.app_context():
        yield _db
