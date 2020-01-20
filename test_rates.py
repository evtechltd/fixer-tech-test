import os
import tempfile
from datetime import datetime, timedelta

import pytest
from flask_migrate import upgrade
from flask_sqlalchemy import SQLAlchemy
from dateutil import parser

from app import app, Rate


@pytest.fixture
def test_app():
    db_fd, db_file = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_file}"
    app.config["TESTING"] = True

    with app.app_context():
        upgrade()
    yield (app)

    os.close(db_fd)
    os.unlink(db_file)


@pytest.fixture
def client(test_app):
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def db(test_app):
    test_db = SQLAlchemy(test_app)
    yield test_db


@pytest.fixture
def rates_data(db):
    test_date = datetime.utcnow().date() - timedelta(days=1)
    new_rates = [
        Rate(currency="GBP", date=test_date, rate="1.2"),
        Rate(currency="AUD", date=test_date, rate="0.9"),
    ]
    db.session.add_all(new_rates)
    db.session.commit()
    yield new_rates


def test_rates_endpoint_fails_gracefully_with_non_date_input(client):
    res = client.get("/rates/not_a_date/")
    assert res.status_code == 400
    assert res.json == {
        "error": "Invalid date - please provide a date in the past, in the format YYYY-MM-DD"
    }


def test_rates_endpoint_fails_gracefully_with_invalid_date_input(client):
    res = client.get("/rates/2020-99-99/")
    assert res.status_code == 400
    assert res.json == {
        "error": "Invalid date - please provide a date in the past, in the format YYYY-MM-DD"
    }


def test_rates_endpoint_fails_gracefully_with_future_date_input(client):
    future_date = datetime.utcnow().date() + timedelta(days=1)
    res = client.get(f"/rates/{future_date.isoformat()}/")
    assert res.status_code == 400
    assert res.json == {
        "error": "Invalid date - please provide a date in the past, in the format YYYY-MM-DD"
    }


def test_rates_endpoint_returns_404_for_a_date_missing_data(client):
    res = client.get("/rates/2020-01-01/")
    assert res.status_code == 404


def test_rates_endpoint_returns_correct_data_for_date(client, rates_data):
    test_date = rates_data[0].date
    res = client.get(f"/rates/{test_date.isoformat()}/")
    assert res.status_code == 200
    assert res.json == {
        "date": test_date.isoformat(),
        "currency_rates": {rate.currency: rate.rate for rate in rates_data},
    }
