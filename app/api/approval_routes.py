
"""API endpoints for human approval decisions."""

from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.api.auth import (
    AuthenticatedPrincipal,
    require_authenticated_principal,
    require_supervisor,
)
from app.config.settings import settings
from app.decision.approval_repository import ApprovalRepository


router = APIRouter(
    prefix="/api/v1/approvals",
    tags=["Approvals"],
)


class ApprovalDecisionRequest(BaseModel):
    """Validate an approval or rejection request."""

    approved: bool = Field(strict=True)
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason")
    @classmethod
    def reject_blank_reason(cls, value: str) -> str:
        """Reject reasons containing only whitespace."""
        value = value.strip()
        if not value:
            raise ValueError("Decision reason must not be blank.")
        return value


class ApprovalResponse(BaseModel):
    """Represent the persisted approval state."""

    id: int
    request_id: str
    status: Literal["PENDING", "APPROVED", "REJECTED"]
    approver: str | None
    reason: str
    decided_at: str | None
    created_at: str


@lru_cache(maxsize=1)
def get_approval_repository() -> ApprovalRepository:
    """Create and reuse the approval repository."""
    return ApprovalRepository(settings.APPROVAL_DATABASE_PATH)


@router.get("/{request_id}", response_model=ApprovalResponse)
def get_approval_status(
    request_id: str,
    repository: ApprovalRepository = Depends(get_approval_repository),
    principal: AuthenticatedPrincipal = Depends(
        require_authenticated_principal
    ),
) -> ApprovalResponse:
    """Retrieve the latest approval record for an investigation."""
    # The principal is required for authentication. Status is readable by
    # authenticated users; decision-making is restricted to supervisors.
    _ = principal

    record = repository.get_latest(request_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="No approval record exists for this request ID.",
        )

    return ApprovalResponse(**record)


@router.post(
    "/{request_id}/decision",
    response_model=ApprovalResponse,
)
def decide_approval(
    request_id: str,
    request: ApprovalDecisionRequest,
    repository: ApprovalRepository = Depends(get_approval_repository),
    principal: AuthenticatedPrincipal = Depends(require_supervisor),
) -> ApprovalResponse:
    """Record a decision using the authenticated supervisor's identity."""
    record = repository.get_latest(request_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="No approval record exists for this request ID.",
        )

    if record["status"] != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="This approval has already been decided.",
        )

    try:
        result = repository.decide(
            record["id"],
            approver=principal.identity,
            approved=request.approved,
            reason=request.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return ApprovalResponse(**result)
