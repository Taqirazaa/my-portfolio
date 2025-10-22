from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from blockguard.config import settings
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize resources here (e.g., vector store warmup)
    yield
    # Cleanup resources


def create_app() -> FastAPI:
    app = FastAPI(
        title="BlockGuard – Agentic AI Auditing",
        version="0.1.0",
        description="Agentic AI-driven auditing for blockchain systems",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
