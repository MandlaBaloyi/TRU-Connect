"""
Top-level API registration.

Every domain exposes its own Blueprint.
This file combines them into a single API blueprint.
"""

from flask import Blueprint

api_bp = Blueprint("api", __name__)

from src.domains.auth.api import auth_bp

api_bp.register_blueprint(auth_bp, url_prefix="/auth")

from src.domains.platform.api.health_routes import health_bp

api_bp.register_blueprint(health_bp, url_prefix="/health")
