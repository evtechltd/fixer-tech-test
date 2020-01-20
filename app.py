import re
import requests
from datetime import datetime, timedelta

from flask import Flask, jsonify
from flask_dotenv import DotEnv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dateutil.parser import parse as dt_parse, _parser

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/rates.db"
env = DotEnv(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


###
# ROUTES
###


@app.route("/rates/<date>/", methods=["GET"])
def rates(date):
    # Validate input
    try:
        assert re.match(r"\d\d\d\d-\d\d-\d\d", date)
        rates_date = dt_parse(date).date()
        assert rates_date <= datetime.utcnow().date()
    except (_parser.ParserError, AssertionError):
        return (
            jsonify(
                {
                    "error": "Invalid date - please provide a date in the past, in the format YYYY-MM-DD"
                }
            ),
            400,
        )

    # Retrieve rates from the database
    daily_rates = db.session.query(Rate).filter(Rate.date == rates_date).all()

    # If rates are unavailable, return a 404
    if len(daily_rates) == 0:
        return jsonify({"date": date, "currency_rates": {}}), 404

    # Return rate data
    rate_data = {rate.currency: rate.rate for rate in daily_rates}
    response = {"date": date, "currency_rates": rate_data}
    return jsonify(response)


###
# MODELS
###


class Rate(db.Model):
    """
    Rate for a specific currency on a specific date
    """

    __tablename__ = "rate"

    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(3), nullable=False, index=True)
    date = db.Column(db.Date(), nullable=False, index=True)
    rate = db.Column(db.Float, nullable=False)

    __table_args__ = (db.UniqueConstraint("currency", "date", name="uq_currency_date"),)


###
# COMMANDS
###


@app.cli.command("ingest_rates")
def ingest_rates():
    """
    Command to get currency rates for the 10 dates previous to today and persist them to the database
    """
    api_key = app.config["FIXER_KEY"]
    symbols = app.config["CURRENCIES"]

    query_string = f"?access_key={api_key}&symbols={symbols}"

    date_today = datetime.utcnow().date()

    rates = []
    for i in range(1, 11):
        # We need to run through the daily endpoints one by one
        try:
            date = date_today - timedelta(days=i)
            endpoint = f"{app.config['FIXER_ENDPOINT']}/{date.isoformat()}{query_string}"
            res = requests.get(endpoint)
            res.raise_for_status()
            data = res.json()

            # Only write new rates if they don't already exist
            for currency, rate in data["rates"].items():
                if (
                    db.session.query(Rate)
                    .filter(Rate.currency == currency)
                    .filter(Rate.date == date)
                    .first()
                    is None
                ):
                    db.session.add(Rate(currency=currency, date=date, rate=rate))

        # If the request for a single day fails, continue with the rest of the days
        except requests.exceptions.HTTPError:
            print(f"Request for date {date} failed, moving on")
            continue

    db.session.commit()
