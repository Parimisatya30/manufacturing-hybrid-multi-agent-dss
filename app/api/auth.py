"""Demo supervisor-ID authentication for local assignment use."""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from app.config.settings import settings


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Supervisor identity resolved by the server."""

    identity: str
    role: str


def require_authenticated_principal(
    supervisor_id: str | None = Header(default=None, alias="X-Supervisor-ID"),
) -> AuthenticatedPrincipal:
    """Validate the demo supervisor ID configured on the server.

    A numeric ID alone is not strong authentication. This is intended only
    for a local assignment/demo, not production deployment.
    """
    if not supervisor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supervisor ID is required.",
        )

    if supervisor_id.strip() != settings.APPROVAL_SUPERVISOR_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supervisor ID.",
        )

    return AuthenticatedPrincipal(
        identity=f"supervisor-{supervisor_id.strip()}",
        role="supervisor",
    )


def require_supervisor(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
) -> AuthenticatedPrincipal:
    """Allow only the configured supervisor to make approval decisions."""
    if principal.role != "supervisor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor role is required for approval decisions.",
        )
    return principal