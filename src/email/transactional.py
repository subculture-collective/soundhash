"""Transactional email helpers for common use cases."""

import logging
from src.email.service import email_service

logger = logging.getLogger(__name__)


async def send_welcome_email(user_email: str, username: str, user_id: int) -> bool:
    """
    Send welcome email to new user.

    Args:
        user_email: User's email address
        username: User's username
        user_id: User ID

    Returns:
        True if email sent successfully
    """
    context = {
        "username": username,
        "email": user_email,
    }

    return await email_service.send_template_email(
        recipient_email=user_email,
        template_name="welcome",
        context=context,
        user_id=user_id,
    )


async def send_password_reset_email(
    user_email: str, username: str, reset_token: str, user_id: int
) -> bool:
    """
    Send password reset email.

    Args:
        user_email: User's email address
        username: User's username
        reset_token: Password reset token
        user_id: User ID

    Returns:
        True if email sent successfully
    """
    app_url = email_service.template_engine.get_base_context()["app_url"]
    context = {
        "username": username,
        "reset_token": reset_token,
        "reset_url": f"{app_url}/reset-password?token={reset_token}",
    }

    return await email_service.send_template_email(
        recipient_email=user_email,
        template_name="password_reset",
        context=context,
        user_id=user_id,
    )


async def send_api_key_generated_email(
    user_email: str, username: str, key_name: str, key_prefix: str, user_id: int
) -> bool:
    """
    Send email when new API key is generated.

    Args:
        user_email: User's email address
        username: User's username
        key_name: Name of the API key
        key_prefix: Prefix of the API key
        user_id: User ID

    Returns:
        True if email sent successfully
    """
    context = {
        "username": username,
        "key_name": key_name,
        "key_prefix": key_prefix,
    }

    return await email_service.send_template_email(
        recipient_email=user_email,
        template_name="api_key_generated",
        context=context,
        user_id=user_id,
    )


async def send_security_alert_email(
    user_email: str, username: str, alert_type: str, alert_details: str, user_id: int
) -> bool:
    """
    Send security alert email.

    Args:
        user_email: User's email address
        username: User's username
        alert_type: Type of security alert
        alert_details: Details of the alert
        user_id: User ID

    Returns:
        True if email sent successfully
    """
    context = {
        "username": username,
        "alert_type": alert_type,
        "alert_details": alert_details,
    }

    return await email_service.send_template_email(
        recipient_email=user_email,
        template_name="security_alert",
        context=context,
        user_id=user_id,
    )


async def send_match_found_email(
    user_email: str,
    username: str,
    match_video_title: str,
    match_video_url: str,
    similarity_score: float,
    user_id: int,
) -> bool:
    """
    Send email when audio match is found.

    Args:
        user_email: User's email address
        username: User's username
        match_video_title: Title of matched video
        match_video_url: URL of matched video
        similarity_score: Match similarity score
        user_id: User ID

    Returns:
        True if email sent successfully
    """
    context = {
        "username": username,
        "video_title": match_video_title,
        "video_url": match_video_url,
        "similarity_score": f"{similarity_score * 100:.1f}%",
    }

    return await email_service.send_template_email(
        recipient_email=user_email,
        template_name="match_found",
        context=context,
        user_id=user_id,
    )


async def send_processing_complete_email(
    user_email: str,
    username: str,
    job_type: str,
    job_details: str,
    user_id: int,
) -> bool:
    """
    Send email when processing job completes.

    Args:
        user_email: User's email address
        username: User's username
        job_type: Type of processing job
        job_details: Details about the job
        user_id: User ID

    Returns:
        True if email sent successfully
    """
    context = {
        "username": username,
        "job_type": job_type,
        "job_details": job_details,
    }

    return await email_service.send_template_email(
        recipient_email=user_email,
        template_name="processing_complete",
        context=context,
        user_id=user_id,
    )


async def send_quota_warning_email(
    user_email: str,
    username: str,
    quota_type: str,
    usage_percentage: float,
    user_id: int,
) -> bool:
    """
    Send email when user approaches quota limit.

    Args:
        user_email: User's email address
        username: User's username
        quota_type: Type of quota (e.g., 'API requests', 'Storage')
        usage_percentage: Percentage of quota used
        user_id: User ID

    Returns:
        True if email sent successfully
    """
    context = {
        "username": username,
        "quota_type": quota_type,
        "usage_percentage": f"{usage_percentage:.0f}%",
    }

    return await email_service.send_template_email(
        recipient_email=user_email,
        template_name="quota_warning",
        context=context,
        user_id=user_id,
    )
