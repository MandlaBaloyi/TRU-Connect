"""
Logging configuration.
 "Production logging".
"""
from __future__ import annotations

import logging

from flask import Flask


def configure_logging(app: Flask) -> None:
    """Configures root logging once per app instance. Debug-level in
    development/testing, info-level in production, so noisy SQL/debug
    logs never ship to production by accident."""
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(log_level)
