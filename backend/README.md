# TRU Connect Backend

Flask + PostgreSQL backend for TRU Connect. Implements the App
Factory, Repository, and Service Layer patterns -- see the backend
master prompt and docs/05_BACKEND_API_SPECIFICATION.txt.

## Status

Foundation only (Steps 1-4): Configuration Layer, Extensions, App
Factory, Database Connection base mixin. No models, repositories,
services, or routes exist yet -- those begin at Step 5 (User
Model) of the phased authentication plan.

## Setup

```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in real values
```

Create the database (once), then run migrations. Flask's CLI and
python-dotenv auto-load your .env file, so these just work once
FLASK_APP is set:

```
export FLASK_APP=app.py         # Windows (PowerShell): $env:FLASK_APP = "app.py"
flask db init                   # first time only
flask db migrate -m "initial"
flask db upgrade
```

Run the server:

```
python app.py
```

## Documentation

Source-of-truth documents live in ../docs -- particularly
docs/04_DATABASE_DESIGN.txt, docs/05_BACKEND_API_SPECIFICATION.txt,
and docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt.
