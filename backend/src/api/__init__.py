"""
Top-level API registration.

Every domain exposes its own Blueprint.
This file combines them into a single API blueprint.
"""

from flask import Blueprint

api_bp = Blueprint("api", __name__)

from src.domains.auth.api import auth_bp

api_bp.register_blueprint(auth_bp, url_prefix="/auth")

# The BROWSER's auth, mounted beside the app's rather than inside it.
# /auth stays the mobile contract exactly as shipped; /auth/web sets
# cookies, enforces CSRF, and turns `business` accounts away. Two
# clients that genuinely behave differently, two routes -- see
# web_routes.py's own docstring.
#
# The prefix is load-bearing, not cosmetic: JWT_REFRESH_COOKIE_PATH is
# "/api/v1/auth/web", so the long-lived refresh cookie is scoped to
# exactly these routes and is not attached to any other API call.
from src.domains.auth.api.web_routes import auth_web_bp

api_bp.register_blueprint(auth_web_bp, url_prefix="/auth/web")

# API key management -- the supplier managing their own machine
# credentials from the portal. Under /supplier because that is whose
# screen it is; the keys themselves authenticate elsewhere, wherever
# @api_key_required is applied.
from src.domains.auth.api_keys.api.api_key_routes import api_keys_bp

api_bp.register_blueprint(api_keys_bp, url_prefix="/supplier")

from src.domains.platform.api.health_routes import health_bp

api_bp.register_blueprint(health_bp, url_prefix="/health")
