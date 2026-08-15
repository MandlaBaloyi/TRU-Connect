"""
Email infrastructure health check.
 "HEALTH CHECK" --
GET /health/email returning Healthy/Unavailable without exposing
credentials.
"""
from __future__ import annotations

from flask import Blueprint

from src.core.responses import error_response, success_response
from src.shared.email.email import EmailService

health_bp = Blueprint("health", __name__)


@health_bp.get("/email")
def email_health():
    if EmailService.health_check():
        return success_response(data={"status": "healthy"}, message="Email infrastructure is healthy.")
    return error_response(message="Email infrastructure is unavailable.", status_code=503)
