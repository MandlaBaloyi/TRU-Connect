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
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "TruConnect <no-reply@truconnect.dev>")
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
    # BOTH LOCATIONS, ON PURPOSE, and this one line is what makes the
    # whole web-portal session work without touching a single existing
    # decorator. flask_jwt_extended looks for the token in each listed
    # location in order and uses whichever it finds: the mobile app
    # keeps sending `Authorization: Bearer`, the browser sends a cookie
    # it cannot read, and @fully_authenticated / @role_required /
    # @verified_required all keep working unchanged for both.
    #
    # Adding "cookies" does NOT make cookies required -- a request with
    # a bearer header and no cookie is still perfectly valid. There is
    # no mobile-facing change here.
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_HEADER_TYPE = "Bearer"

    # --- V2: browser session cookies (supplier web portal) ---
    #
    # WHY COOKIES AND NOT THE BEARER TOKEN THE APP USES. Anything a
    # browser tab can read, an XSS on that page can read -- and a JWT in
    # localStorage is exactly that. An httpOnly cookie is not reachable
    # from JavaScript at all, so a script injected into the portal can
    # still ACT as the user while the page is open, but it cannot steal
    # a credential and replay it later from somewhere else. That
    # difference is the entire point.
    #
    # WHAT COOKIES COST YOU IS CSRF. A browser attaches cookies to a
    # request no matter who caused it, so a form on someone else's site
    # can fire an authenticated request at us. Bearer tokens are immune
    # because nothing attaches them automatically. flask_jwt_extended's
    # double-submit is switched on below: it sets a SECOND, JS-readable
    # cookie and requires its value echoed back in a header, which an
    # attacker's page cannot read cross-origin.
    #
    # HAND-ROLLING THAT WAS THE REJECTED ALTERNATIVE. The library's
    # implementation is enforced ONLY on requests whose token came from
    # a cookie, so mobile never sees a CSRF check -- and CSRF is a thing
    # to be subtly wrong about exactly once.
    JWT_COOKIE_SECURE = os.environ.get("JWT_COOKIE_SECURE", "True").lower() in ("true", "1", "yes")
    JWT_COOKIE_SAMESITE = os.environ.get("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = True
    JWT_ACCESS_CSRF_HEADER_NAME = "X-CSRF-TOKEN"
    JWT_REFRESH_CSRF_HEADER_NAME = "X-CSRF-TOKEN"

    # The API and the portal are different hosts in production
    # (api.truconnect.co.za / portal.truconnect.co.za). The CSRF cookie
    # has to be READABLE by the portal's JavaScript, which means the
    # cookie must be issued for the shared parent domain rather than the
    # API host alone. Left unset in dev: localhost:3000 and
    # localhost:5000 are the same cookie host already (cookies ignore
    # the port), so nothing is needed there.
    JWT_COOKIE_DOMAIN = os.environ.get("JWT_COOKIE_DOMAIN") or None

    # The refresh cookie is scoped to the auth routes instead of "/", so
    # it is simply not attached to the hundreds of ordinary API calls a
    # portal session makes. The one long-lived credential should travel
    # as rarely as possible. Not narrowed to /refresh alone because
    # logout needs it too -- that is what revokes the row.
    JWT_ACCESS_COOKIE_PATH = "/"
    JWT_REFRESH_COOKIE_PATH = "/api/v1/auth/web"

    # SEPARATE LIFETIMES FROM MOBILE, deliberately -- these are read by
    # WebSessionService and passed per-token, they do NOT change the
    # JWT_*_EXPIRES values above that the app runs on.
    #
    # A supplier keeps a portal tab open all day, so 30 minutes of
    # access is fine: the refresh cookie renews it silently and they
    # never see it. 7 days rather than mobile's 30 because a browser
    # session is often on a shared depot machine that the person who
    # signed in has since walked away from; a phone is not.
    WEB_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.environ.get("WEB_ACCESS_TOKEN_EXPIRES_MINUTES", 30))
    )
    WEB_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get("WEB_REFRESH_TOKEN_EXPIRES_DAYS", 7))
    )

    # --- V2: CORS ---
    #
    # NEVER "*", and not out of caution -- a browser refuses to send
    # credentials to a wildcard origin, so a wildcard would break the
    # cookie session outright rather than merely loosen it. An explicit
    # allowlist is the only thing that works AND the only thing that is
    # safe, which is a pleasant coincidence.
    #
    # The mobile app is native, sends no Origin header, and is entirely
    # unaffected by any of this.
    WEB_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("WEB_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]

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
    # A Secure cookie is never sent over plain http, so leaving the
    # production default on here would make the portal silently fail to
    # log in against a local http backend -- with no error, because a
    # cookie the browser refuses to store looks exactly like a cookie
    # the server never set. Overridden here rather than in .env so a
    # forgotten env var cannot ship this to production.
    JWT_COOKIE_SECURE = False


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
    # Same reason as DevelopmentConfig: the test client speaks http.
    JWT_COOKIE_SECURE = False


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