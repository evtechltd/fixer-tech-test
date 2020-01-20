import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import requests
from flask_migrate import upgrade
from flask_sqlalchemy import SQLAlchemy
from click.testing import CliRunner

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
def db(test_app):
    test_db = SQLAlchemy(test_app)
    yield test_db


@pytest.fixture
def ingest_rates(test_app):
    yield test_app.cli.commands["ingest_rates"]


@patch("app.requests.get")
def test_ingest_rates_fails_gracefully_for_bad_get(get_mock, test_app, db, ingest_rates):
    get_mock.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError

    runner = CliRunner()
    res = runner.invoke(ingest_rates)
    assert res.exit_code == 0
    assert "failed" in res.output

    ingested_rates = db.session.query(Rate).all()
    assert len(ingested_rates) == 0


@patch("app.requests.get")
def test_ingest_rates_writes_correctly_for_successful_get(
    get_mock, test_app, db, ingest_rates
):
    get_mock.return_value.json.return_value = {"rates": {"GBP": 1.2, "AUD": 0.9}}

    runner = CliRunner()
    res = runner.invoke(ingest_rates)
    assert res.exit_code == 0
    assert res.output == ""

    ingested_rates = db.session.query(Rate).all()
    assert len(ingested_rates) == 20
