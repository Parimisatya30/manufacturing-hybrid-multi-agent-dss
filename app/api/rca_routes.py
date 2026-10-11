
"""FastAPI route for manufacturing root-cause analysis."""

import logging
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.synthesis.rca_service_factory import create_rca_workflow
from app.workflows.rca_workflow import RCAWorkflow

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/rca",
    tags=["Root Cause Analysis"],
)


class RCARequest(BaseModel):
    """Validate an RCA investigation request."""

    user_query: str = Field(min_length=1, max_length=2000)
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
def get_rca_workflow() -> RCAWorkflow:
    """Create and reuse the RCA workflow within this process."""
    return create_rca_workflow()


@router.post("/investigate")
def investigate_root_cause(
    payload: RCARequest,
    request: Request,
) -> dict[str, Any]:
    """Run an evidence-grounded root-cause investigation."""
    try:
        workflow = get_rca_workflow()
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
            detail="Invalid RCA request.",
        ) from exc

    except Exception as exc:
        logger.exception(
            "RCA investigation failed",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        raise HTTPException(
            status_code=500,
            detail="Root-cause investigation failed.",
        ) from exc
