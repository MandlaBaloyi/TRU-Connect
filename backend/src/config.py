"""
Configuration Layer.


Defines environment-specific configuration classes consumed by the Flask
application factory (src/__init__.py). All secrets and environment-
specific values are read from environment variables (see .env)
-- nothing is ever hard-coded here.

Flask's CLI (and python-dotenv, already in requirements.txt) auto-loads a
.env file in this directory, so `flask db migrate`, `flask run`, and
`python app.py` all pick up the same values without extra setup.
"""
import os
from datetime import timedelta
from urllib.parse import quote  # URL‑encode special characters in the database URI


class BaseConfig:
    """Shared configuration across all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Shared Notification Infrastructure (email) ---
    #
    # "CONFIGURATION". MAIL_PROVIDER defaults to "smtp" (Gmail today);
    # TestingConfig overrides this to "fake" so tests never send real
    # email.
    MAIL_PROVIDER = os.environ.get("MAIL_PROVIDER", "smtp")
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "TRU Connect <no-reply@truconnect.dev>")
    # Where a supplier report actually lands today -- there's no admin
    # panel/control centre built yet to review these in-app, so a real
    # inbox is the honest "someone actually sees this" mechanism until
    # that exists. The report itself is ALSO a real, permanent database
    # row regardless of whether this email ever arrives (see
    # SupplierReport's own docstring) -- this address is a notification
    # on top of that record, never a replacement for it.
    SUPPLIER_REPORTS_EMAIL = os.environ.get("SUPPLIER_REPORTS_EMAIL", "reports@truconnect.dev")
    MAIL_TIMEOUT = int(os.environ.get("MAIL_TIMEOUT", 10))
    MAIL_MAX_RETRIES = int(os.environ.get("MAIL_MAX_RETRIES", 3))
    MAIL_RETRY_DELAYS = [
        int(x) for x in os.environ.get("MAIL_RETRY_DELAY", "5,15,60").split(",") if x.strip()
    ]
    MAIL_ASYNC = os.environ.get("MAIL_ASYNC", "True").lower() in ("true", "1", "yes")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 15))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_TYPE = "Bearer"

    # --- Auth Hardening additions ---
    # Base URL for the password-reset browser bounce page
    # (src/domains/platform/api/reset_redirect_routes.py). In dev, point
    # this at your machine's LAN IP so the emailed link works on a
    # physical phone; in production, your real domain.
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")

    UNVERIFIED_ACCOUNT_EXPIRY_HOURS = int(os.environ.get("UNVERIFIED_ACCOUNT_EXPIRY_HOURS", 24))
    LOGIN_MAX_FAILED_ATTEMPTS = int(os.environ.get("LOGIN_MAX_FAILED_ATTEMPTS", 5))
    LOGIN_LOCKOUT_WINDOW_MINUTES = int(os.environ.get("LOGIN_LOCKOUT_WINDOW_MINUTES", 15))
    PASSWORD_RESET_TICKET_EXPIRY_HOURS = int(os.environ.get("PASSWORD_RESET_TICKET_EXPIRY_HOURS", 1))

    @staticmethod
    def _build_database_uri() -> str:
        """
        Builds a PostgreSQL URI from discrete POSTGRES_* environment
        variables. DATABASE_URL, if set, takes priority over these
        (useful for managed-Postgres providers that hand you one
        connection string directly).

        User and password are URL‑encoded so that special characters
        (e.g. @ in a password) don't break the connection string.
        """
        user = quote(os.environ.get("POSTGRES_USER", "postgres"))
        password = quote(os.environ.get("POSTGRES_PASSWORD", "postgres"))
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = os.environ.get("POSTGRES_PORT", "5432")
        db_name = os.environ.get("POSTGRES_DB", "tru_connect")
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or BaseConfig._build_database_uri()


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/tru_connect_test",
    )
    # Short-lived tokens keep auth tests fast and deliberate about expiry.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    # Never send real email in tests -- FakeEmailProvider records sends
    # in memory instead, and MAIL_ASYNC=False makes send_template() run
    # synchronously so tests can assert against it immediately.
    MAIL_PROVIDER = "fake"
    MAIL_ASYNC = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or BaseConfig._build_database_uri()


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None):
    """Resolve a config class by environment name, defaulting to
    FLASK_ENV (or "development" if that's unset too)."""
    env_name = env_name or os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(env_name, DevelopmentConfig)