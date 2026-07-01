"""FastAPI application entry point."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from home_tutor.api.http.routes import router as http_router
from home_tutor.api.middleware.logging import RequestLoggingMiddleware
from home_tutor.api.webrtc.signaling import router as webrtc_router
from home_tutor.api.websocket.handler import router as ws_router
from home_tutor.core.config import settings
from home_tutor.core.logging import get_logger, log_trace, setup_logging
from home_tutor.models.database import init_db
from home_tutor.services.llm.analysis_service import get_analysis_service
from home_tutor.services.llm.langfuse_tracing import flush_langfuse, init_langfuse

setup_logging(settings)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup and shutdown hooks."""
    init_langfuse()
    await init_db()
    loop = asyncio.get_running_loop()
    get_analysis_service().bind_loop(loop)
    log_trace(
        get_logger(__name__),
        "SERVER_STARTED",
        host=settings.host,
        port=settings.port,
        log_mode=settings.log_mode,
    )
    try:
        yield
    finally:
        flush_langfuse()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(http_router, prefix="/api")
    app.include_router(ws_router)
    app.include_router(webrtc_router, prefix="/api/webrtc")

    return app


app = create_app()


def run_dev() -> None:
    """Run the development server."""
    import uvicorn

    uvicorn.run(
        "home_tutor.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run_dev()
