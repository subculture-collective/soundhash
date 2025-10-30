"""Pydantic models for compliance API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# =====================================================================
# CONSENT MODELS
# =====================================================================


class ConsentCreate(BaseModel):
    """Request model for creating consent record."""

    consent_type: str = Field(..., description="Type of consent")
    consent_version: str = Field(..., description="Version of the document")
    given: bool = Field(True, description="True if consenting, False if withdrawing")
    method: Optional[str] = Field(None, description="Method of consent collection")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class ConsentResponse(BaseModel):
    """Response model for consent record."""

    id: int
    user_id: int
    consent_type: str
    consent_version: str
    given: bool
    given_at: datetime
    withdrawn_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# DATA EXPORT MODELS
# =====================================================================


class DataExportRequestCreate(BaseModel):
    """Request model for data export."""

    request_type: str = Field("full_export", description="Type of export")
    data_types: Optional[list[str]] = Field(None, description="Specific data types to export")
    format: str = Field("json", description="Export format (json, csv, xml)")


class DataExportRequestResponse(BaseModel):
    """Response model for data export request."""

    id: int
    user_id: int
    request_type: str
    format: str
    status: str
    requested_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    download_count: Optional[int] = None

    class Config:
        from_attributes = True


# =====================================================================
# DATA DELETION MODELS
# =====================================================================


class DataDeletionRequestCreate(BaseModel):
    """Request model for data deletion."""

    deletion_type: str = Field("full", description="Type of deletion (full, partial, anonymize)")
    data_types: Optional[list[str]] = Field(None, description="Specific data types to delete")
    reason: Optional[str] = Field(None, description="Reason for deletion")


class DataDeletionRequestResponse(BaseModel):
    """Response model for data deletion request."""

    id: int
    user_id: int
    deletion_type: str
    status: str
    requested_at: datetime
    verified_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verification_token: Optional[str] = None

    class Config:
        from_attributes = True


# =====================================================================
# RETENTION POLICY MODELS
# =====================================================================


class RetentionPolicyCreate(BaseModel):
    """Request model for creating retention policy."""

    policy_name: str = Field(..., description="Name of the policy")
    data_type: str = Field(..., description="Type of data this policy applies to")
    retention_days: int = Field(..., description="Number of days to retain data", gt=0)
    action: str = Field("delete", description="Action after retention period")
    description: Optional[str] = Field(None, description="Policy description")
    legal_basis: Optional[str] = Field(None, description="Legal justification")


class RetentionPolicyResponse(BaseModel):
    """Response model for retention policy."""

    id: int
    policy_name: str
    data_type: str
    retention_days: int
    action: str
    is_active: bool
    created_at: datetime
    last_applied_at: Optional[datetime] = None

    class Config:
        from_attributes = True
