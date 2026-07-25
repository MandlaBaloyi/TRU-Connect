"""
Configuration Layer.
Ref: docs/04_DATABASE_DESIGN.txt, docs/05_BACKEND_API_SPECIFICATION.txt

Defines environment-specific configuration classes consumed by the Flask
application factory (src/__init__.py). All secrets and environment-
specific values are read from environment variables (see .env.example)
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

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 15))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_TYPE = "Bearer"

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