"""
Standard JSON response envelope.
Ref: backend master prompt, "API DESIGN" -- every response follows the
same success/failure shape:

    Success: {"success": true,  "message": "...", "data": {}}
    Failure: {"success": false, "message": "...", "errors": []}

Routes and error handlers call these helpers rather than hand-rolling a
response dict, so the envelope shape can never drift between endpoints.
"""
from __future__ import annotations

from typing import Any

from flask import jsonify


def success_response(data: Any = None, message: str = "Success", status_code: int = 200):
    payload = {"success": True, "message": message, "data": data if data is not None else {}}
    return jsonify(payload), status_code


def error_response(message: str = "An error occurred", errors: list | None = None, status_code: int = 400):
    payload = {"success": False, "message": message, "errors": errors or []}
    return jsonify(payload), status_code
