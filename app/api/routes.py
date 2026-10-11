"""FastAPI routes for the Manufacturing DSS."""

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.synthesis.maintenance_service import MaintenanceService
from app.synthesis.service_factory import create_maintenance_service


router = APIRouter(
    prefix="/api/v1/maintenance",
    tags=["Maintenance"],
)


class MaintenanceInvestigationRequest(BaseModel):
    """Validate incoming maintenance investigation requests."""

    machine_id: int = Field(gt=0)
    user_query: str = Field(min_length=1, max_length=2000)
    request_id: str | None = Field(default=None, max_length=100)

    @field_validator("user_query")
    @classmethod
    def validate_user_query(cls, value: str) -> str:
        """Reject queries containing only whitespace."""
        if not value.strip():
            raise ValueError("user_query must not be blank")

        return value.strip()

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, value: str | None) -> str | None:
        """Reject blank or malformed request IDs."""
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("request_id must not be blank")

        if not value.replace("-", "").replace("_", "").isalnum():
            raise ValueError("request_id contains invalid characters")

        return value


class MaintenanceInvestigationResponse(BaseModel):
    """Response containing the decision and synthesized explanation."""

    decision: dict[str, Any]
    response: dict[str, Any]


@lru_cache(maxsize=1)
def get_maintenance_service() -> MaintenanceService:
    """Create and reuse one maintenance service per application process."""
    return create_maintenance_service()


@router.post(
    "/investigate",
    response_model=MaintenanceInvestigationResponse,
)
def investigate_maintenance(
    request: MaintenanceInvestigationRequest,
    service: MaintenanceService | None = Depends(get_maintenance_service),
) -> MaintenanceInvestigationResponse:
    """Investigate a machine and return an evidence-grounded response."""

    # Return 503 if the service is deliberately unavailable.
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Maintenance service has not been configured.",
        )

    try:
        result = service.investigate(
            machine_id=request.machine_id,
            user_query=request.user_query,
            request_id=request.request_id,
        )

        return MaintenanceInvestigationResponse(**result)

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid maintenance investigation request.",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Maintenance investigation failed.",
        ) from exc