# Fixer Data Processor

## Intro
This is a simple Flask app to ingest currency data from [Fixer](http://fixer.io), persist it to a database, then serve it via an HTTP API.

## Structure
All app logic is in `app.py` - the structure is intentionally naive due to the simplicity of the app.  The tests are found in `test_*.py` files, to be discoverable by pytest.

## Routes
The app only has a single route, the rates endpoint: `/rates/<date>/`.  `<date>` is an isoformat date, eg `2020-01-01`.

## Commands
The app has a single command, which persists the previous 10 days of currency data to the database.  The command is `flask ingest_rates`, and has no arguments.

## Deployment
Clone the project, copy the `.env.example` to `.env` and update file with your Fixer credentials. In a shell, create a virtual environment using Python 3.7 or above, and install the requirements into it:

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Initialise the database using Flask-migrate:

```sh
flask db upgrade
```

Populate the database with recent data using the `ingest_rates` CLI command, and run the app to expose the data on the API:

```sh
flask ingest_rates
flask run
```

## Running the tests
After setting up the app (as in the Deployment section above), run the tests using pytest:

```sh
pytest
```

## Improvements
- The structure of the app as it is is very naive - beyond this level of complexity, the app logic needs to be split out of the `app.py` file, at least into separate `models.py`, `routes.py`, and `commands.py` files.  Beyond this, using the Flask blueprint functionality would improve the internal structure, and splitting these files further would also help handle more complexity.
- The app itself is initialised in a very simplistic way, which suits this exercise, but would be improved by use of the Flask factory pattern to initialise extensions.
- The database shouldn't be running locally in memory.  The best solution for this app would probably be a cloud-based solution, either SQL or not (RDS / DynamoDB or equivalent), depending on the future use case of the app.
- The code should run on multiple workers using Gunicorn or similar to scale better.
- A layer of authentication / authorization would be necessary for API users in production.
- The test fixtures could probably be simplified somewhat, and more and better test data could be added.
- The ingest command should have more flexibility in which days it can collect, ie taking command line arguments for the number of days or for specific dates.
- Failed requests to the Fixer API should be handled better, preferable with backed off retries.
- If necessary, the ingest command could be moved to a scheduler / queue to run at a set frequency and keep the data up to date automatically.
- The ingest command should check data that already exists against data it's received for the same date and update it (assuming that newer data for the same date in Fixer is more accurate).

## CI, Deployment and Monitoring in production
In a theoretical production environment, the app should have a CI pipeline (my preference is for CircleCI, but the individual provider isn't massively important).  The CI should, at the least, lint the code and run the tests and alert if either step fails.  Deploying the code into production could be done in lots of different ways.  As an example, a successful CI run on the Master branch could save an artifact and trigger a Packer build using Ansible to configure the hardware, pulling the artifact and creating an AMI on AWS EC2.  A separate Terraform app could use that new AMI to create an autoscaling launch group, pushing the new code live, switching DNS, and pulling down the machines.

This is one specific example using AWS EC2, but there are plenty of other options to choose from. Different cloud providers (GCP, Azure), different paradigms (eg serverless, docker + kubernetes, managed platforms like Heroku), and different automation systems could all be valid choices, depending on factors around the application itself.

Similarly, the possible choices for monitoring the application are numerous.  Generally, I'd like to spread the monitoring vertically over the infrastructure and software, from exception alerting for individual errors (eg Sentry) to monitoring of the characteristics of the infrastructure the app is running on (eg Cloudwatch).  Between these there are plenty of other sources of information to either aggregate or process - the app logs themselves, logs from the persistent layer, logs from a webserver layer (eg nginx), etc.