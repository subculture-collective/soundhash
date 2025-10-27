"""Common Pydantic models for API responses."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    """Error detail model."""

    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    details: list[ErrorDetail] | None = None
    request_id: str | None = None


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated response wrapper."""

    data: list[DataT]
    total: int
    page: int
    per_page: int
    total_pages: int


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime | None = None


class IDMixin(BaseModel):
    """Mixin for ID field."""

    id: int
