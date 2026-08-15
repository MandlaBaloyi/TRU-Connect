"""
Standard JSON response envelope.


    Success: {"success": true,  "message": "...", "data": {}}
    Failure: {"success": false, "message": "...", "errors": [],
              "code": "...", "data": {}}   <- code/data optional

`code` and the failure-side `data` are additive: existing callers that
only pass message/errors/status_code are completely unaffected.
"""
from __future__ import annotations

from typing import Any, Optional

from flask import jsonify


def success_response(data: Any = None, message: str = "Success", status_code: int = 200):
    payload = {"success": True, "message": message, "data": data if data is not None else {}}
    return jsonify(payload), status_code


def error_response(
    message: str = "An error occurred",
    errors: Optional[list] = None,
    status_code: int = 400,
    code: Optional[str] = None,
    data: Optional[dict] = None,
):
    payload: dict = {"success": False, "message": message, "errors": errors or []}
    if code is not None:
        payload["code"] = code
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code
