"""
trigger.start()/stop() — proves double-start is a no-op, and the
Werkzeug-reloader-watcher-process guard correctly skips starting in the
parent process while allowing it in the real worker process (or in any
non-debug run).
"""

from __future__ import annotations

import os

import pytest
from flask import Flask

from src.domains.platform.schedulers import trigger


@pytest.fixture(autouse=True)
def _reset_trigger_state():
    trigger.stop()
    yield
    trigger.stop()


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)


def _make_app(debug: bool) -> Flask:
    app = Flask(__name__)
    app.debug = debug
    return app


def test_start_is_idempotent():
    app = _make_app(debug=False)
    trigger.start(app)
    assert trigger.is_running() is True
    trigger.start(app)  # second call must be a no-op, not raise or double-start
    assert trigger.is_running() is True


def test_skips_start_in_reloader_watcher_process(monkeypatch):
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)
    app = _make_app(debug=True)  # debug on, reloader active, WERKZEUG_RUN_MAIN unset = watcher process
    trigger.start(app)
    assert trigger.is_running() is False


def test_starts_in_reloader_worker_process(monkeypatch):
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "true")
    app = _make_app(debug=True)
    trigger.start(app)
    assert trigger.is_running() is True


def test_starts_normally_when_debug_is_off():
    app = _make_app(debug=False)
    trigger.start(app)
    assert trigger.is_running() is True
