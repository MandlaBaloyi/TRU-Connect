"""
Application Factory.
App Factory".
"""
from __future__ import annotations
from flask import Flask
from src.config import get_config
from src.extensions import db, migrate, jwt, ma
from src.shared.logging.logger import configure_logging


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
        "TruConnect backend initialised (env=%s)", env_name or app.config.get("ENV", "development")
    )

    from src.domains.security.audit.services import audit_service
    audit_service.register(app)

    from src.master_scheduler import trigger
    trigger.start(app)

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    from src.domains.security.rate_limit.limiter import limiter
    limiter.init_app(app)


def _register_blueprints(app: Flask) -> None:
    from src.api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    from src.domains.platform.api.reset_password_routes import reset_password_bp
    app.register_blueprint(reset_password_bp)

    from src.domains.business.loan_book.api.loan_book_routes import loan_book_bp
    app.register_blueprint(loan_book_bp)

    from src.domains.business.order_book.api.order_book_routes import order_book_bp
    app.register_blueprint(order_book_bp)

    from src.domains.business.business_profile.api.business_profile_routes import business_profile_bp
    app.register_blueprint(business_profile_bp)


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
        return error_response(
            message=error.message,
            errors=error.errors,
            status_code=error.status_code,
            code=error.code,
            data=error.data,
        )

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

    from src.domains.security.rate_limit import responses as rate_limit_responses
    from src.domains.auth.rate_limit.policies import RATE_LIMIT_AUDIT_EVENTS as AUTH_RATE_LIMIT_AUDIT_EVENTS
    rate_limit_responses.register_audit_events(AUTH_RATE_LIMIT_AUDIT_EVENTS)
    # Future domains' own rate_limit/policies.py RATE_LIMIT_AUDIT_EVENTS
    # get registered here the same way, e.g.:
    #   from src.domains.business.order_book.rate_limit.policies import RATE_LIMIT_AUDIT_EVENTS as ORDER_BOOK_...
    #   rate_limit_responses.register_audit_events(ORDER_BOOK_...)
    rate_limit_responses.register(app)