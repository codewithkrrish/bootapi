"""Health endpoints — the first thing your load balancer and your
monitoring will call, so they stay boring and fast."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from ..config import Settings, get_settings
from ..deps import get_store
from ..models import HealthStatus
from ..store import Store

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
def health(settings: Settings = Depends(get_settings)) -> HealthStatus:
    """Liveness: "is the process up?" Always cheap, never touches the DB."""
    return HealthStatus(
        status="ok", app=settings.app_name, version=settings.app_version
    )


@router.get("/health/ready")
def ready(store: Store = Depends(get_store)) -> dict[str, str]:
    """Readiness: "can this instance actually serve traffic?"

    Returns 503 while the database doesn't answer, so a broken deploy
    never gets traffic routed to it.
    """
    if not store.ping():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready"},
        )
    return {"status": "ready"}
