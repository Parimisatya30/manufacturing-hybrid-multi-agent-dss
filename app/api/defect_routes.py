
"""FastAPI routes for manufacturing defect monitoring."""

import logging
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.synthesis.defect_service_factory import (
    create_defect_monitoring_workflow,
)
from app.workflows.defect_monitoring_workflow import (
    DefectMonitoringWorkflow,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/defects",
    tags=["Defect Monitoring"],
)


class DefectMonitoringRequest(BaseModel):
    """Validate a defect-monitoring request."""

    user_query: str = Field(
        default="Monitor manufacturing defects",
        min_length=1,
        max_length=2000,
    )
    request_id: str | None = Field(default=None, max_length=100)

    @field_validator("user_query")
    @classmethod
    def validate_user_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("user_query must not be blank")
        return value.strip()

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("request_id must not be blank")

        if not value.replace("-", "").replace("_", "").isalnum():
            raise ValueError("request_id contains invalid characters")

        return value


@lru_cache(maxsize=1)
def get_defect_monitoring_workflow() -> DefectMonitoringWorkflow:
    """Create and reuse the workflow within this application process."""
    return create_defect_monitoring_workflow()


@router.post("/monitor")
def monitor_defects(
    payload: DefectMonitoringRequest,
    request: Request,
) -> dict[str, Any]:
    """Return defect metrics, rule evaluations, and supporting evidence."""

    try:
        workflow = get_defect_monitoring_workflow()

        request_id = (
            payload.request_id
            or getattr(request.state, "request_id", None)
        )

        return workflow.run(
            user_query=payload.user_query,
            request_id=request_id,
        )

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid defect-monitoring request.",
        ) from exc

    except Exception as exc:
        logger.exception(
            "Defect-monitoring request failed",
            extra={
                "request_id": getattr(request.state, "request_id", None)
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Defect-monitoring investigation failed.",
        ) from exc