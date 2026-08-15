# TRU Connect Backend

Flask + PostgreSQL backend for TRU Connect. Implements the App


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


