"""Tests for data retention service."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.compliance.retention import DataRetentionService
from src.database.models import AuditLog, EmailLog


def test_create_retention_policy(db_session: Session):
    """Test creating a retention policy."""
    policy = DataRetentionService.create_policy(
        policy_name="Audit Log Retention",
        data_type="audit_logs",
        retention_days=365,
        action="delete",
        description="Retain audit logs for 1 year",
        legal_basis="SOC 2 compliance requirement",
        session=db_session,
    )

    assert policy is not None
    assert policy.policy_name == "Audit Log Retention"
    assert policy.data_type == "audit_logs"
    assert policy.retention_days == 365
    assert policy.action == "delete"
    assert policy.is_active is True


def test_list_retention_policies(db_session: Session):
    """Test listing retention policies."""
    # Create multiple policies
    DataRetentionService.create_policy(
        policy_name="Policy 1",
        data_type="audit_logs",
        retention_days=365,
        session=db_session,
    )

    DataRetentionService.create_policy(
        policy_name="Policy 2",
        data_type="email_logs",
        retention_days=90,
        session=db_session,
    )

    policies = DataRetentionService.list_policies(session=db_session)
    assert len(policies) >= 2


def test_get_retention_policy(db_session: Session):
    """Test retrieving a specific retention policy."""
    created_policy = DataRetentionService.create_policy(
        policy_name="Test Policy",
        data_type="test_data",
        retention_days=30,
        session=db_session,
    )

    retrieved_policy = DataRetentionService.get_policy(created_policy.id, session=db_session)
    assert retrieved_policy is not None
    assert retrieved_policy.id == created_policy.id
    assert retrieved_policy.policy_name == "Test Policy"


def test_deactivate_retention_policy(db_session: Session):
    """Test deactivating a retention policy."""
    policy = DataRetentionService.create_policy(
        policy_name="To Deactivate",
        data_type="test_data",
        retention_days=30,
        session=db_session,
    )

    success = DataRetentionService.deactivate_policy(policy.id, session=db_session)
    assert success is True

    db_session.refresh(policy)
    assert policy.is_active is False


def test_apply_audit_log_retention_policy(db_session: Session):
    """Test applying retention policy for audit logs."""
    # Create old audit logs
    old_date = datetime.utcnow() - timedelta(days=400)
    for i in range(5):
        audit_log = AuditLog(
            action=f"old_action_{i}",
            status="success",
            created_at=old_date,
        )
        db_session.add(audit_log)
    db_session.commit()

    # Create recent audit logs
    recent_date = datetime.utcnow() - timedelta(days=10)
    for i in range(3):
        audit_log = AuditLog(
            action=f"recent_action_{i}",
            status="success",
            created_at=recent_date,
        )
        db_session.add(audit_log)
    db_session.commit()

    # Create retention policy (365 days)
    DataRetentionService.create_policy(
        policy_name="Audit Log Cleanup",
        data_type="audit_logs",
        retention_days=365,
        action="delete",
        session=db_session,
    )

    # Apply policies
    results = DataRetentionService.apply_policies(session=db_session)

    # Verify old logs deleted
    assert results["audit_logs"] == 5

    # Verify recent logs still exist
    recent_logs = db_session.query(AuditLog).filter(
        AuditLog.action.like("recent_action_%")
    ).all()
    assert len(recent_logs) == 3


def test_apply_email_log_retention_policy(db_session: Session):
    """Test applying retention policy for email logs."""
    # Create old email logs
    old_date = datetime.utcnow() - timedelta(days=100)
    for i in range(3):
        email_log = EmailLog(
            recipient_email=f"old_{i}@test.com",
            subject="Old Email",
            status="sent",
            created_at=old_date,
        )
        db_session.add(email_log)
    db_session.commit()

    # Create recent email logs
    recent_date = datetime.utcnow() - timedelta(days=10)
    for i in range(2):
        email_log = EmailLog(
            recipient_email=f"recent_{i}@test.com",
            subject="Recent Email",
            status="sent",
            created_at=recent_date,
        )
        db_session.add(email_log)
    db_session.commit()

    # Create retention policy (90 days)
    DataRetentionService.create_policy(
        policy_name="Email Log Cleanup",
        data_type="email_logs",
        retention_days=90,
        action="delete",
        session=db_session,
    )

    # Apply policies
    results = DataRetentionService.apply_policies(session=db_session)

    # Verify old logs deleted
    assert results["email_logs"] == 3

    # Verify recent logs still exist
    recent_logs = db_session.query(EmailLog).filter(
        EmailLog.recipient_email.like("recent_%")
    ).all()
    assert len(recent_logs) == 2


def test_retention_policy_last_applied_timestamp(db_session: Session):
    """Test that last_applied_at is updated when policy is applied."""
    policy = DataRetentionService.create_policy(
        policy_name="Test Timestamp",
        data_type="audit_logs",
        retention_days=365,
        session=db_session,
    )

    assert policy.last_applied_at is None

    # Apply policies
    DataRetentionService.apply_policies(session=db_session)

    # Refresh and check timestamp
    db_session.refresh(policy)
    assert policy.last_applied_at is not None
