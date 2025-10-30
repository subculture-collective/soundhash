"""Tests for audit logging service."""

from sqlalchemy.orm import Session

from src.compliance.audit_logger import AuditLogger
from src.database.models import AuditLog


def test_log_action_basic(db_session: Session):
    """Test basic audit log creation."""
    audit_entry = AuditLogger.log_action(
        action="test.action",
        user_id=1,
        resource_type="test_resource",
        resource_id="123",
        status="success",
        session=db_session,
    )

    assert audit_entry is not None
    assert audit_entry.action == "test.action"
    assert audit_entry.user_id == 1
    assert audit_entry.resource_type == "test_resource"
    assert audit_entry.resource_id == "123"
    assert audit_entry.status == "success"


def test_log_action_with_metadata(db_session: Session):
    """Test audit log with metadata."""
    metadata = {"key": "value", "count": 42}
    audit_entry = AuditLogger.log_action(
        action="test.action_with_metadata",
        user_id=1,
        metadata=metadata,
        session=db_session,
    )

    assert audit_entry is not None
    assert audit_entry.extra_metadata == metadata


def test_log_action_with_changes(db_session: Session):
    """Test audit log with old and new values."""
    old_values = {"name": "Old Name", "value": 100}
    new_values = {"name": "New Name", "value": 200}

    audit_entry = AuditLogger.log_action(
        action="test.update",
        user_id=1,
        resource_type="test_resource",
        resource_id="456",
        old_values=old_values,
        new_values=new_values,
        status="success",
        session=db_session,
    )

    assert audit_entry is not None
    assert audit_entry.old_values == old_values
    assert audit_entry.new_values == new_values


def test_log_data_access(db_session: Session):
    """Test convenience method for logging data access."""
    audit_entry = AuditLogger.log_data_access(
        user_id=1,
        resource_type="user",
        resource_id="789",
        ip_address="192.168.1.1",
        session=db_session,
    )

    assert audit_entry is not None
    assert audit_entry.action == "user.read"
    assert audit_entry.ip_address == "192.168.1.1"


def test_log_data_modification(db_session: Session):
    """Test convenience method for logging data modification."""
    old_data = {"status": "inactive"}
    new_data = {"status": "active"}

    audit_entry = AuditLogger.log_data_modification(
        user_id=1,
        resource_type="user",
        resource_id="789",
        old_values=old_data,
        new_values=new_data,
        session=db_session,
    )

    assert audit_entry is not None
    assert audit_entry.action == "user.update"
    assert audit_entry.old_values == old_data
    assert audit_entry.new_values == new_data


def test_log_data_deletion(db_session: Session):
    """Test convenience method for logging data deletion."""
    old_data = {"id": 789, "name": "Deleted User"}

    audit_entry = AuditLogger.log_data_deletion(
        user_id=1,
        resource_type="user",
        resource_id="789",
        old_values=old_data,
        session=db_session,
    )

    assert audit_entry is not None
    assert audit_entry.action == "user.delete"
    assert audit_entry.old_values == old_data


def test_audit_log_persisted(db_session: Session):
    """Test that audit log is properly persisted to database."""
    AuditLogger.log_action(
        action="test.persistence",
        user_id=1,
        resource_type="test",
        resource_id="999",
        session=db_session,
    )

    # Query the database to verify persistence
    audit_entry = db_session.query(AuditLog).filter_by(action="test.persistence").first()
    assert audit_entry is not None
    assert audit_entry.resource_id == "999"
