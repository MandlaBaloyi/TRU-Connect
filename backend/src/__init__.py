"""
Application Factory.
Ref: backend master prompt, "Step 3: App Factory".

create_app() builds and configures a Flask application instance. Routes
are intentionally not registered with real logic yet -- src/api/__init__.py
currently exposes an empty blueprint; Authentication routes begin at
Step 7 (Registration) of the phased plan.
"""
from __future__ import annotations

from flask import Flask

from src.config import get_config
from src.extensions import db, migrate, jwt, ma
from src.utils.logger import configure_logging


def create_app(env_name: str | None = None) -> Flask:
    """Flask App Factory. Pass env_name explicitly in tests (e.g.
    create_app("testing")); everywhere else it falls back to FLASK_ENV."""
    app = Flask(__name__)
    app.config.from_object(get_config(env_name))

    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    configure_logging(app)
    app.logger.info(
        "TRU Connect backend initialised (env=%s)", env_name or app.config.get("ENV", "development")
    )

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)


def _register_blueprints(app: Flask) -> None:
    from src.api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api/v1")


def _register_error_handlers(app: Flask) -> None:
    """
    Converts any AppError raised by a service (see src/core/exceptions.py)
    into the standard JSON envelope defined in
    docs/05_BACKEND_API_SPECIFICATION.txt, Section 1 -- routes never need
    to catch these individually.
    """
    from src.core.exceptions import AppError
    from src.core.responses import error_response

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return error_response(message=error.message, errors=error.errors, status_code=error.status_code)

    @app.errorhandler(404)
    def handle_not_found(_error):
        return error_response(message="Resource not found", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        return error_response(message="Method not allowed", status_code=405)

    @app.errorhandler(500)
    def handle_internal_error(error):
        app.logger.exception("Unhandled server error: %s", error)
        return error_response(message="Internal server error", status_code=500)
