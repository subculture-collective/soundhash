"""Email notification system."""

from src.email.service import EmailService, email_service
from src.email.templates import EmailTemplateEngine
from src.email.transactional import (
    send_api_key_generated_email,
    send_match_found_email,
    send_password_reset_email,
    send_processing_complete_email,
    send_quota_warning_email,
    send_security_alert_email,
    send_welcome_email,
)

__all__ = [
    "EmailService",
    "email_service",
    "EmailTemplateEngine",
    "send_welcome_email",
    "send_password_reset_email",
    "send_api_key_generated_email",
    "send_security_alert_email",
    "send_match_found_email",
    "send_processing_complete_email",
    "send_quota_warning_email",
]
