"""FastAPI routes for the Manufacturing DSS."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.synthesis.maintenance_service import MaintenanceService


router = APIRouter(
    prefix="/api/v1/maintenance",
    tags=["Maintenance"],
)


class MaintenanceInvestigationRequest(BaseModel):
    """Request to investigate a manufacturing machine."""

    machine_id: int = Field(gt=0)
    user_query: str = Field(min_length=1, max_length=2000)
    request_id: str | None = Field(default=None, max_length=100)

    @field_validator("user_query")
    @classmethod
    def validate_user_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("user_query must not be blank")
        return value.strip()


class MaintenanceInvestigationResponse(BaseModel):
    """Decision and synthesized response from an investigation."""

    decision: dict[str, Any]
    response: dict[str, Any]


def get_maintenance_service() -> MaintenanceService | None:
    """Provide the service; configure it before serving investigations."""
    return None


@router.post(
    "/investigate",
    response_model=MaintenanceInvestigationResponse,
)
def investigate_maintenance(
    request: MaintenanceInvestigationRequest,
    service: MaintenanceService | None = Depends(get_maintenance_service),
) -> MaintenanceInvestigationResponse:
    """Run a maintenance investigation and synthesize its response."""

    # Request validation happens before this check.
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Maintenance investigation failed.",
        ) from exc