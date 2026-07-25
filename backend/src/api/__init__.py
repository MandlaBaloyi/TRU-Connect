"""
API Blueprint Registration.
Ref: backend master prompt, "FOLDER STRUCTURE" -- routes only validate
request, call service, return response; no database or business logic
inside routes.

No route modules exist yet -- Authentication routes begin at Step 7
(Registration) of the phased plan (docs/05_BACKEND_API_SPECIFICATION.txt,
Section 5.1). This blueprint is registered by the app factory now so
later route modules have a stable place to attach to without touching
src/__init__.py again.
"""
from flask import Blueprint

api_bp = Blueprint("api", __name__)

from src.api.auth_routes import auth_bp

api_bp.register_blueprint(auth_bp, url_prefix="/auth")
