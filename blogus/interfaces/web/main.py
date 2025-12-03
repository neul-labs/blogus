"""
Main FastAPI application for Blogus web service.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routers import prompts, registry, prompt_files
from .container import get_container
from ...shared.exceptions import BlogusError, ValidationError, ResourceNotFoundError
from ...shared.logging import setup_logging, get_logger


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Blogus API",
        description="API for crafting, analyzing, and perfecting AI prompts",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Setup CORS for Vue.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers (unified prompts router handles both prompts and templates)
    app.include_router(prompts.router, prefix="/api/v1")
    app.include_router(registry.router, prefix="/api/v1")
    app.include_router(prompt_files.router, prefix="/api/v1")  # File-based prompts

    return app


app = create_app()


@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={"error": "Validation Error", "detail": str(exc)}
    )


@app.exception_handler(ResourceNotFoundError)
async def not_found_error_handler(request, exc: ResourceNotFoundError):
    """Handle resource not found errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Resource Not Found", "detail": str(exc)}
    )


@app.exception_handler(BlogusError)
async def blogus_error_handler(request, exc: BlogusError):
    """Handle general Blogus errors."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Error", "detail": str(exc)}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Blogus API", "version": "1.0.0", "docs": "/api/docs"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "blogus-api"}


def main():
    """Run the FastAPI server."""
    setup_logging()
    logger = get_logger("blogus.web")

    container = get_container()
    settings = container.settings

    logger.info(f"Starting Blogus web service on {settings.web.host}:{settings.web.port}")

    uvicorn.run(
        "blogus.interfaces.web.main:app",
        host=settings.web.host,
        port=settings.web.port,
        reload=settings.web.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()