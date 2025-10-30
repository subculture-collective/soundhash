"""Compliance and privacy API routes (GDPR, CCPA, SOC 2)."""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.models.compliance import (
    ConsentCreate,
    ConsentResponse,
    DataDeletionRequestCreate,
    DataDeletionRequestResponse,
    DataExportRequestCreate,
    DataExportRequestResponse,
    RetentionPolicyCreate,
    RetentionPolicyResponse,
)
from src.compliance.audit_logger import AuditLogger
from src.compliance.consent_manager import ConsentManager
from src.compliance.data_deletion import DataDeletionService
from src.compliance.data_export import DataExportService
from src.compliance.retention import DataRetentionService
from src.database.models import User

router = APIRouter()

# Initialize services
data_export_service = DataExportService()
data_deletion_service = DataDeletionService()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# =====================================================================
# USER CONSENT ENDPOINTS
# =====================================================================


@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def record_consent(
    consent_data: ConsentCreate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Record user consent (GDPR requirement)."""
    consent = ConsentManager.record_consent(
        user_id=current_user.id,
        consent_type=consent_data.consent_type,
        consent_version=consent_data.consent_version,
        given=consent_data.given,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        method=consent_data.method or "api",
        metadata=consent_data.metadata,
        session=db,
    )

    return ConsentResponse(
        id=consent.id,
        user_id=consent.user_id,
        consent_type=consent.consent_type,
        consent_version=consent.consent_version,
        given=consent.given,
        given_at=consent.given_at,
        withdrawn_at=consent.withdrawn_at,
        created_at=consent.created_at,
    )


@router.delete("/consent/{consent_type}", status_code=status.HTTP_200_OK)
async def withdraw_consent(
    consent_type: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Withdraw previously given consent."""
    success = ConsentManager.withdraw_consent(
        user_id=current_user.id,
        consent_type=consent_type,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        session=db,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active consent found for type: {consent_type}",
        )

    return {"message": "Consent withdrawn successfully", "consent_type": consent_type}


@router.get("/consent/{consent_type}", status_code=status.HTTP_200_OK)
async def check_consent(
    consent_type: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Check if user has given consent for a specific type."""
    has_consent = ConsentManager.check_consent(
        user_id=current_user.id, consent_type=consent_type, session=db
    )

    return {"consent_type": consent_type, "has_consent": has_consent}


@router.get("/consent", response_model=list[ConsentResponse])
async def get_consent_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    consent_type: Optional[str] = None,
):
    """Get consent history for the current user."""
    consents = ConsentManager.get_consent_history(
        user_id=current_user.id, consent_type=consent_type, session=db
    )

    return [
        ConsentResponse(
            id=c.id,
            user_id=c.user_id,
            consent_type=c.consent_type,
            consent_version=c.consent_version,
            given=c.given,
            given_at=c.given_at,
            withdrawn_at=c.withdrawn_at,
            created_at=c.created_at,
        )
        for c in consents
    ]


# =====================================================================
# DATA EXPORT ENDPOINTS (GDPR Article 15)
# =====================================================================


@router.post(
    "/data-export",
    response_model=DataExportRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_data_export(
    export_data: DataExportRequestCreate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Request data export (GDPR Article 15 - Right to access)."""
    export_request = data_export_service.create_export_request(
        user_id=current_user.id,
        request_type=export_data.request_type,
        data_types=export_data.data_types,
        format=export_data.format,
        ip_address=get_client_ip(request),
        session=db,
    )

    return DataExportRequestResponse(
        id=export_request.id,
        user_id=export_request.user_id,
        request_type=export_request.request_type,
        format=export_request.format,
        status=export_request.status,
        requested_at=export_request.requested_at,
        expires_at=export_request.expires_at,
    )


@router.get("/data-export/{request_id}", response_model=DataExportRequestResponse)
async def get_data_export_status(
    request_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get status of a data export request."""
    from src.database.models import DataExportRequest

    export_request = db.query(DataExportRequest).filter_by(id=request_id).first()

    if not export_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export request not found"
        )

    if export_request.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return DataExportRequestResponse(
        id=export_request.id,
        user_id=export_request.user_id,
        request_type=export_request.request_type,
        format=export_request.format,
        status=export_request.status,
        requested_at=export_request.requested_at,
        completed_at=export_request.completed_at,
        expires_at=export_request.expires_at,
        file_size_bytes=export_request.file_size_bytes,
        download_count=export_request.download_count,
    )


@router.post("/data-export/{request_id}/process", status_code=status.HTTP_200_OK)
async def process_data_export(
    request_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Process a pending data export request (admin/background job)."""
    from src.database.models import DataExportRequest

    export_request = db.query(DataExportRequest).filter_by(id=request_id).first()

    if not export_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export request not found"
        )

    if export_request.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    file_path = data_export_service.process_export_request(request_id, session=db)

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process export request",
        )

    return {"message": "Export processed successfully", "file_path": file_path}


# =====================================================================
# DATA DELETION ENDPOINTS (GDPR Article 17)
# =====================================================================


@router.post(
    "/data-deletion",
    response_model=DataDeletionRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_data_deletion(
    deletion_data: DataDeletionRequestCreate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Request data deletion (GDPR Article 17 - Right to be forgotten)."""
    deletion_request = data_deletion_service.create_deletion_request(
        user_id=current_user.id,
        deletion_type=deletion_data.deletion_type,
        data_types=deletion_data.data_types,
        reason=deletion_data.reason,
        ip_address=get_client_ip(request),
        session=db,
    )

    return DataDeletionRequestResponse(
        id=deletion_request.id,
        user_id=deletion_request.user_id,
        deletion_type=deletion_request.deletion_type,
        status=deletion_request.status,
        requested_at=deletion_request.requested_at,
        verification_token=deletion_request.verification_token,
    )


@router.post("/data-deletion/{request_id}/verify", status_code=status.HTTP_200_OK)
async def verify_data_deletion(
    request_id: int,
    verification_token: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Verify a data deletion request."""
    success = data_deletion_service.verify_deletion_request(
        request_id=request_id, verification_token=verification_token, session=db
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token or request not found",
        )

    return {"message": "Deletion request verified", "request_id": request_id}


@router.get("/data-deletion/{request_id}", response_model=DataDeletionRequestResponse)
async def get_data_deletion_status(
    request_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get status of a data deletion request."""
    from src.database.models import DataDeletionRequest

    deletion_request = db.query(DataDeletionRequest).filter_by(id=request_id).first()

    if not deletion_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deletion request not found"
        )

    if deletion_request.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return DataDeletionRequestResponse(
        id=deletion_request.id,
        user_id=deletion_request.user_id,
        deletion_type=deletion_request.deletion_type,
        status=deletion_request.status,
        requested_at=deletion_request.requested_at,
        verified_at=deletion_request.verified_at,
        completed_at=deletion_request.completed_at,
    )


# =====================================================================
# DATA RETENTION POLICY ENDPOINTS (Admin only)
# =====================================================================


@router.post(
    "/retention-policies",
    response_model=RetentionPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_retention_policy(
    policy_data: RetentionPolicyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a data retention policy (Admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    policy = DataRetentionService.create_policy(
        policy_name=policy_data.policy_name,
        data_type=policy_data.data_type,
        retention_days=policy_data.retention_days,
        action=policy_data.action,
        description=policy_data.description,
        legal_basis=policy_data.legal_basis,
        tenant_id=current_user.tenant_id,
        session=db,
    )

    return RetentionPolicyResponse(
        id=policy.id,
        policy_name=policy.policy_name,
        data_type=policy.data_type,
        retention_days=policy.retention_days,
        action=policy.action,
        is_active=policy.is_active,
        created_at=policy.created_at,
    )


@router.get("/retention-policies", response_model=list[RetentionPolicyResponse])
async def list_retention_policies(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all retention policies (Admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    policies = DataRetentionService.list_policies(tenant_id=current_user.tenant_id, session=db)

    return [
        RetentionPolicyResponse(
            id=p.id,
            policy_name=p.policy_name,
            data_type=p.data_type,
            retention_days=p.retention_days,
            action=p.action,
            is_active=p.is_active,
            created_at=p.created_at,
            last_applied_at=p.last_applied_at,
        )
        for p in policies
    ]


@router.post("/retention-policies/apply", status_code=status.HTTP_200_OK)
async def apply_retention_policies(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Apply all active retention policies (Admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    results = DataRetentionService.apply_policies(tenant_id=current_user.tenant_id, session=db)

    return {"message": "Retention policies applied", "results": results}


@router.delete("/retention-policies/{policy_id}", status_code=status.HTTP_200_OK)
async def deactivate_retention_policy(
    policy_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Deactivate a retention policy (Admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    success = DataRetentionService.deactivate_policy(policy_id, session=db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Retention policy not found"
        )

    return {"message": "Retention policy deactivated", "policy_id": policy_id}
