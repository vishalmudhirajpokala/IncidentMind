"""IncidentMind API.

Layering, outermost first:

    api/routes      HTTP surface, no business logic
    services        orchestration and business rules
    repositories    data access, returns SQLModel instances
    models          persistence schema
    integrations    vendor adapters behind provider interfaces

Provider-specific code stops at ``app/integrations``. A dead external service
degrades a response, it does not produce a 500.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_agent, routes_demo, routes_incidents, routes_memory, routes_metrics
from app.config import settings
from app.database import create_all, session_scope
from app.repositories.incident_repository import IncidentRepository
from app.schemas.system import HealthResponse
from app.utils.logging import (
    configure_logging,
    get_logger,
    get_request_id,
    new_request_id,
    set_request_id,
)
from seed.seed_incidents import seed_incidents

configure_logging(level=settings.LOG_LEVEL, json_output=settings.LOG_JSON)
log = get_logger("app")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Prepare the schema on start-up so a fresh checkout runs immediately."""
    create_all()

    # An empty database is seeded with the reference corpus outside
    # production, so the demo has real history to recall on a cold start.
    # This is fixture data and is logged as such; it is never seeded in prod.
    if settings.APP_ENV != "production":
        try:
            with session_scope() as session:
                if IncidentRepository(session).count() == 0:
                    created = seed_incidents(session)
                    log.info(
                        "empty database seeded with the reference corpus",
                        extra={"event_incidents_seeded": created},
                    )
        except Exception as exc:  # noqa: BLE001
            # Seeding is a convenience. A failure here must not stop the API.
            log.warning("reference seeding skipped", extra={"event_error": type(exc).__name__})
    yield


app = FastAPI(
    title="IncidentMind API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    description=(
        "A memory-first incident response agent. The loop is: investigate an "
        "incident, recall how this organisation has seen it before, recommend a "
        "reversible action, have a human approve it, then retain the outcome so "
        "the next similar incident starts from experience rather than from zero.\n\n"
        "**All actions are simulated.** This API never executes a real "
        "infrastructure change; it requires explicit human approval and returns "
        "deterministic simulated telemetry."
    ),
    openapi_tags=[
        {"name": "incidents", "description": "Incident CRUD and history."},
        {"name": "agent", "description": "Investigate, approve, resolve, retain."},
        {"name": "memory", "description": "Organisational memory recall and status."},
        {"name": "metrics", "description": "Counts derived from the database."},
        {"name": "demo", "description": "Deterministic learning-loop demo."},
        {"name": "system", "description": "Health and readiness."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next: Callable) -> JSONResponse:
    """Attach a correlation id to every request and log the outcome."""
    request_id = request.headers.get("X-Request-ID") or new_request_id()
    set_request_id(request_id)
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled error", extra={"event_path": request.url.path})
        raise

    duration_ms = int((time.perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = request_id

    log.info(
        "request",
        extra={
            "event_method": request.method,
            "event_path": request.url.path,
            "event_status": response.status_code,
            "event_duration_ms": duration_ms,
        },
    )
    return response


# Routers carry relative prefixes; /api is applied once, here.
app.include_router(routes_incidents.router, prefix="/api")
app.include_router(routes_agent.router, prefix="/api")
app.include_router(routes_memory.router, prefix="/api")
app.include_router(routes_metrics.router, prefix="/api")
app.include_router(routes_demo.router, prefix="/api")


@app.get("/", tags=["system"], summary="Service description")
def root() -> Dict[str, Any]:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "/api/health",
            "incidents": "/api/incidents",
            "investigate": "/api/incidents/{id}/investigate",
            "simulate_action": "/api/incidents/{id}/simulate-action",
            "resolve": "/api/incidents/{id}/resolve",
            "retain": "/api/incidents/{id}/retain",
            "memory_recall": "/api/memory/recall",
            "memory_recent": "/api/memory/recent",
            "metrics": "/api/metrics/overview",
            "demo_scenarios": "/api/demo/scenarios",
            "demo_run": "/api/demo/run",
            "demo_reset": "/api/demo/reset",
        },
        "safety": (
            "All actions are simulated and require explicit human approval. "
            "This service never executes a real infrastructure change."
        ),
    }


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health, with per-dependency detail",
    description=(
        "Always returns 200. An optional dependency being down is reported in "
        "the response body, not turned into a failed request, so orchestration "
        "does not restart a healthy process over a degraded optional service."
    ),
)
def health() -> HealthResponse:
    from app.integrations.factory import get_llm_provider, get_memory_provider
    from app.schemas.memory import ProviderStatus
    from app.database import session_scope
    from sqlalchemy import text

    # --- database -------------------------------------------------------
    try:
        with session_scope() as session:
            session.exec(text("SELECT 1"))
        database = ProviderStatus(
            name="database", mode="live", available=True, detail=settings.DATABASE_URL.split("://")[0]
        )
    except Exception as exc:  # noqa: BLE001
        database = ProviderStatus(
            name="database", mode="unavailable", available=False, detail=type(exc).__name__
        )

    # --- memory ---------------------------------------------------------
    try:
        from sqlmodel import Session

        from app.database import engine

        with Session(engine) as session:
            memory_provider, _fallback, _mode = get_memory_provider(session)
            memory = memory_provider.health()
    except Exception as exc:  # noqa: BLE001
        memory = ProviderStatus(
            name="memory", mode="unavailable", available=False, detail=type(exc).__name__
        )

    # --- llm ------------------------------------------------------------
    try:
        llm_provider, _fallback, _mode = get_llm_provider()
        llm = llm_provider.health()
    except Exception as exc:  # noqa: BLE001
        llm = ProviderStatus(
            name="llm", mode="unavailable", available=False, detail=type(exc).__name__
        )

    degraded = not (database.available and memory.available and llm.available)

    return HealthResponse(
        # "ok" means the process is serving requests. "degraded" means it is
        # serving, but at least one optional dependency is not answering.
        status="ok" if not degraded else "degraded",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
        demo_mode=settings.DEMO_MODE,
        database=database,
        memory=memory,
        llm=llm,
    )
