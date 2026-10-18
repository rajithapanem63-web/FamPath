"""
Celery email tasks: verification email, password reset, workspace invitation.
"""
from __future__ import annotations

import smtplib
from typing import Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.workers.celery_app import celery_app
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

_jinja = Environment(
    loader=FileSystemLoader("app/workers/templates"),
    autoescape=select_autoescape(["html"]),
)


def _send_email(to_email: str, subject: str, html_body: str) -> None:
    """Send an email via SMTP. Raises on failure."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USER:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email(
    self: Any,
    to_email: str,
    full_name: str,
    token: str,
    locale: str = "en",
) -> None:
    """Send account verification email."""
    try:
        template = _jinja.get_template(f"verify_email_{locale}.html")
        body = template.render(
            full_name=full_name,
            verification_url=f"{_get_frontend_url()}/verify-email?token={token}",
        )
        _send_email(to_email, _SUBJECTS["verify_email"][locale], body)
        logger.info("verification_email_sent", email=to_email)
    except Exception as exc:
        logger.error("verification_email_failed", email=to_email, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(
    self: Any,
    to_email: str,
    token: str,
    locale: str = "en",
) -> None:
    """Send password reset email."""
    try:
        template = _jinja.get_template(f"password_reset_{locale}.html")
        body = template.render(
            reset_url=f"{_get_frontend_url()}/reset-password?token={token}",
        )
        _send_email(to_email, _SUBJECTS["password_reset"][locale], body)
        logger.info("password_reset_email_sent", email=to_email)
    except Exception as exc:
        logger.error("password_reset_email_failed", email=to_email, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_workspace_invitation_email(
    self: Any,
    to_email: str,
    invited_by_name: str,
    workspace_name: str,
    token: str,
    locale: str = "en",
) -> None:
    """Send workspace invitation email."""
    try:
        template = _jinja.get_template(f"workspace_invite_{locale}.html")
        body = template.render(
            invited_by_name=invited_by_name,
            workspace_name=workspace_name,
            accept_url=f"{_get_frontend_url()}/workspace/accept?token={token}",
        )
        _send_email(to_email, _SUBJECTS["workspace_invite"][locale], body)
        logger.info("invite_email_sent", email=to_email)
    except Exception as exc:
        logger.error("invite_email_failed", email=to_email, error=str(exc))
        raise self.retry(exc=exc)


def _get_frontend_url() -> str:
    return "https://fampath.in"  # overridden by env var FAMPATH_FRONTEND_URL in production


_SUBJECTS: dict[str, dict[str, str]] = {
    "verify_email": {
        "en": "Verify your FamPath email address",
        "te": "మీ FamPath ఇమెయిల్ చిరునామాను ధృవీకరించండి",
        "hi": "अपना FamPath ईमेल पता सत्यापित करें",
    },
    "password_reset": {
        "en": "Reset your FamPath password",
        "te": "మీ FamPath పాస్‌వర్డ్‌ని రీసెట్ చేయండి",
        "hi": "अपना FamPath पासवर्ड रीसेट करें",
    },
    "workspace_invite": {
        "en": "You've been invited to a FamPath family workspace",
        "te": "మీరు FamPath ఫ్యామిలీ వర్క్‌స్పేస్‌కు ఆహ్వానించబడ్డారు",
        "hi": "आपको FamPath फैमिली वर्कस्पेस में आमंत्रित किया गया है",
    },
}
