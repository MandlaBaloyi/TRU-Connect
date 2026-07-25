"""
TRU Connect Backend -- entry point.

Development:
    python app.py

Production (example): gunicorn / any WSGI server pointed at `app:app`,
e.g.:
    gunicorn "app:app" --bind 0.0.0.0:8000 --workers 4
"""
import os

from src import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config.get("DEBUG", False),
    )
