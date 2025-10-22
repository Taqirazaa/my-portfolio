from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.audit import router as audit_router
from app.api.routes.reports import router as reports_router
from app.api.routes.agents import router as agents_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"]) 
api_router.include_router(ingest_router, prefix="/ingest", tags=["ingest"]) 
api_router.include_router(audit_router, prefix="/audit", tags=["audit"]) 
api_router.include_router(reports_router, prefix="/reports", tags=["reports"]) 
api_router.include_router(agents_router, prefix="/agents", tags=["agents"]) 