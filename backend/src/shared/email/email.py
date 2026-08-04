

"""
Email Service and Provider abstraction.
"Shared Notification Infrastructure" -- this is the
ONLY file in the entire backend allowed to import smtplib. Every domain
(auth, business, supplier, ...) calls EmailService.send_template() and
nothing else; none of them know or care that Gmail SMTP is behind it
today, or that SES/SendGrid/etc. might be behind it tomorrow.
"""
from __future__ import annotations

import logging
import os
import smtplib
import time
from abc import ABC, abstractmethod
from email.message import EmailMessage
from typing import Optional

from flask import current_app
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.shared.cache.cache import check_rate_limit
from src.shared.constants.constants import (
    DEFAULT_MAIL_MAX_RETRIES,
    DEFAULT_MAIL_RETRY_DELAYS_SECONDS,
    DEFAULT_MAIL_TIMEOUT_SECONDS,
    MailProvider,
)
from src.shared.helpers.helpers import mask_email
from src.shared.logging.metrics import Timer, metrics
from src.shared.monitoring.monitoring import (
    log_email_failed,
    log_email_queued,
    log_email_sent,
    log_rate_limit_exceeded,
    log_retry_scheduled,
    log_smtp_auth_failure,
)
from src.shared.queue.queue import enqueue

logger = logging.getLogger("tru_connect.email")

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
_jinja_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=select_autoescape(["html"]))


# ------------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------------

class EmailSendError(Exception):
    """Raised by an EmailProvider on a (presumed transient) send failure
    -- EmailService retries on this."""


class EmailAuthenticationError(EmailSendError):
    """Raised specifically for provider credential failures -- NOT
    retried (wrong credentials will still be wrong on the next attempt),
    logged via log_smtp_auth_failure() which deliberately never includes
    the credentials themselves."""


# ------------------------------------------------------------------------
# Provider abstraction
# ------------------------------------------------------------------------

class EmailProvider(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str, text_body: Optional[str] = None) -> None:
        """Raises EmailSendError (or EmailAuthenticationError) on
        failure; returns None on success."""

    @abstractmethod
    def check_connection(self) -> bool:
        """Lightweight connectivity check for the /health/email
        endpoint -- must never send an actual email."""


class SMTPEmailProvider(EmailProvider):
    """Works with Gmail SMTP today (MAIL_SERVER=smtp.gmail.com) and any
    other standards-compliant SMTP server -- including SES/SendGrid/
    Mailgun/Azure's own SMTP relay endpoints, which all support this
    exact protocol, in addition to their non-SMTP APIs. This is why SMTP
    alone already gets most of the way to "production ready" without
    writing provider-specific code -- true native-API integrations
    (e.g. for better deliverability analytics) are a future upgrade of
    THIS class alone, never of its callers.
    """

    def __init__(
        self,
        host: str,
        port: int,
        use_tls: bool,
        username: str,
        password: str,
        default_sender: str,
        timeout: int,
    ):
        self._host = host
        self._port = port
        self._use_tls = use_tls
        self._username = username
        self._password = password
        self._default_sender = default_sender
        self._timeout = timeout

    def _connect(self) -> smtplib.SMTP:
        server = smtplib.SMTP(self._host, self._port, timeout=self._timeout)
        if self._use_tls:
            server.starttls()
        if self._username and self._password:
            server.login(self._username, self._password)
        return server

    def send(self, to: str, subject: str, html_body: str, text_body: Optional[str] = None) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._default_sender
        message["To"] = to
        message.set_content(text_body or "This email requires an HTML-capable email client to view.")
        message.add_alternative(html_body, subtype="html")

        try:
            with self._connect() as server:
                server.send_message(message)
        except smtplib.SMTPAuthenticationError as exc:
            raise EmailAuthenticationError(str(exc)) from exc
        except (smtplib.SMTPException, OSError, TimeoutError) as exc:
            raise EmailSendError(str(exc)) from exc

    def check_connection(self) -> bool:
        try:
            with self._connect():
                pass
            return True
        except smtplib.SMTPAuthenticationError:
            log_smtp_auth_failure()
            return False
        except (smtplib.SMTPException, OSError, TimeoutError):
            return False


class FakeEmailProvider(EmailProvider):
    """Dev/test provider -- records every "sent" email in memory instead
    of contacting any real server. Used when MAIL_PROVIDER=fake (see
    src/config.py's TestingConfig)."""

    def __init__(self):
        self.sent_emails: list[dict] = []

    def send(self, to: str, subject: str, html_body: str, text_body: Optional[str] = None) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "html_body": html_body, "text_body": text_body})

    def check_connection(self) -> bool:
        return True

    def clear(self) -> None:
        self.sent_emails.clear()


_fake_provider_singleton = FakeEmailProvider()


def get_fake_provider() -> FakeEmailProvider:
    """Test helper -- returns the same FakeEmailProvider instance
    EmailService uses whenever MAIL_PROVIDER=fake, so tests can assert
    against sent_emails."""
    return _fake_provider_singleton


def _resolve_provider() -> EmailProvider:
    provider_name = current_app.config.get("MAIL_PROVIDER", MailProvider.SMTP.value)
    if provider_name == MailProvider.FAKE.value:
        return _fake_provider_singleton

    # SES / SendGrid / Mailgun / Azure are reserved MailProvider values
    # for when a native-API integration is added later -- only SMTP is
    # implemented today (see SMTPEmailProvider's own docstring for why
    # that already covers real production providers via their SMTP
    # relays, not just Gmail).
    return SMTPEmailProvider(
        host=current_app.config["MAIL_SERVER"],
        port=current_app.config["MAIL_PORT"],
        use_tls=current_app.config["MAIL_USE_TLS"],
        username=current_app.config["MAIL_USERNAME"],
        password=current_app.config["MAIL_PASSWORD"],
        default_sender=current_app.config["MAIL_DEFAULT_SENDER"],
        timeout=current_app.config.get("MAIL_TIMEOUT", DEFAULT_MAIL_TIMEOUT_SECONDS),
    )


def _render_template(template_name: str, context: dict) -> str:
    template = _jinja_env.get_template(template_name)
    return template.render(**context)


def _send_with_retry(
    provider: EmailProvider,
    to: str,
    subject: str,
    html_body: str,
    template_name: str,
    destination_masked: str,
    max_retries: int,
    retry_delays: list,
) -> None:
    for attempt in range(1, max_retries + 1):
        try:
            with Timer() as timer:
                provider.send(to, subject, html_body)
            metrics.record_send_duration(timer.elapsed_seconds)
            metrics.record_sent(template_name)
            log_email_sent(destination_masked, template_name, timer.elapsed_seconds)
            return
        except EmailAuthenticationError:
            # Wrong credentials -- retrying will not help.
            log_smtp_auth_failure()
            metrics.record_failed(template_name)
            return
        except EmailSendError as exc:
            metrics.record_retry(template_name)
            if attempt < max_retries:
                delay = retry_delays[min(attempt - 1, len(retry_delays) - 1)]
                log_retry_scheduled(destination_masked, template_name, attempt, delay)
                time.sleep(delay)
            else:
                log_email_failed(destination_masked, template_name, str(exc))
                metrics.record_failed(template_name)


class EmailService:
    """The ONLY thing any domain should ever call. Never raises --
    failures are logged and metriced, never propagated (master prompt,
    "FAILURE POLICY": "Email failures must never crash the application.
    Registration should still succeed.")."""

    @staticmethod
    def send_template(
        to: str,
        template_name: str,
        subject: str,
        context: dict,
        rate_limit_key: Optional[str] = None,
        rate_limit_max: Optional[int] = None,
        rate_limit_window_seconds: int = 3600,
    ) -> None:
        destination_masked = mask_email(to)

        if rate_limit_key and rate_limit_max is not None:
            if not check_rate_limit(rate_limit_key, rate_limit_max, rate_limit_window_seconds):
                log_rate_limit_exceeded(destination_masked, template_name)
                return

        try:
            html_body = _render_template(template_name, context)
        except Exception:  # noqa: BLE001 - template errors must not break the caller
            logger.exception("Failed to render email template %s", template_name)
            return

        try:
            provider = _resolve_provider()
        except KeyError:
            logger.error(
                "Email not sent: MAIL_* configuration is incomplete (template=%s). "
                "Check backend/.env for MAIL_SERVER/MAIL_PORT/MAIL_USE_TLS/"
                "MAIL_USERNAME/MAIL_PASSWORD/MAIL_DEFAULT_SENDER.",
                template_name,
            )
            return

        max_retries = current_app.config.get("MAIL_MAX_RETRIES", DEFAULT_MAIL_MAX_RETRIES)
        retry_delays = current_app.config.get("MAIL_RETRY_DELAYS", DEFAULT_MAIL_RETRY_DELAYS_SECONDS)
        is_async = current_app.config.get("MAIL_ASYNC", True)

        log_email_queued(destination_masked, template_name)

        def _job() -> None:
            _send_with_retry(
                provider, to, subject, html_body, template_name, destination_masked, max_retries, retry_delays
            )

        if is_async:
            enqueue(_job)
        else:
            _job()

    @staticmethod
    def health_check() -> bool:
        """Backs GET /health/email. Never raises, never exposes
        credentials -- returns True (healthy) or False (unavailable)."""
        try:
            provider = _resolve_provider()
            return provider.check_connection()
        except Exception:  # noqa: BLE001
            logger.exception("Email health check failed")
            return False
