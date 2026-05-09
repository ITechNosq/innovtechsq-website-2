"""
InnovTech Sq Lead Capture API - PRODUCTION SECURED
Production-ready FastAPI backend with security hardening.

SECURITY FEATURES:
- CORS restricted to specific origins
- Request logging with correlation IDs
- Secure error handling
- Health check with DB connectivity
- All secrets from environment variables
"""
import time
import uuid
from contextlib import asynccontextmanager
from typing import Generator

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import sys

from app.core.config import settings
from app.database import init_db, get_db as original_get_db
from app.routes import lead, auth

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    if settings.DEBUG:
        logger.warning("DEBUG mode enabled - NOT for production!")
    
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Check CORS configuration
    cors_origins = settings.get_cors_origins()
    if not cors_origins:
        logger.warning("CORS not configured - no origins allowed!")
    else:
        logger.info(f"CORS allowed origins: {cors_origins}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SECURE API for capturing leads from InnovTech Sq website",
    lifespan=lifespan
)


# ============== SECURITY MIDDLEWARE ==============

# CORS - RESTRICTED to specific origins (no wildcards!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept", "Origin"],
)


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with correlation ID."""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request
        logger.info(
            f"[{request_id}] {method} {path} - "
            f"{response.status_code} - {duration:.3f}s - "
            f"IP: {client_ip}"
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"[{request_id}] {method} {path} - "
            f"500 ERROR - {duration:.3f}s - "
            f"IP: {client_ip} - {e}"
        )
        raise


# ============== EXCEPTION HANDLERS ==============

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors - don't expose internal details."""
    request_id = str(uuid.uuid4())[:8]
    logger.warning(f"[{request_id}] Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request",
            "error_code": "VALIDATION_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors - generic message to client."""
    request_id = str(uuid.uuid4())[:8]
    # Log full error internally
    logger.error(f"[{request_id}] Unhandled error: {exc}")
    # Return generic message
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


# ============== DATABASE HEALTH CHECK ==============

def get_db_health():
    """Database health check dependency."""
    from sqlalchemy import text
    db = next(original_get_db())
    try:
        db.execute(text("SELECT 1"))
        yield db
    finally:
        db.close()


# ============== INCLUDE ROUTES ==============

app.include_router(auth.router)
app.include_router(lead.router)


# ============== HEALTH CHECK ==============

@app.get("/health")
async def health_check(db=Depends(get_db_health)):
    """
    Health check endpoint.
    Checks both API and database connectivity.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected"
    }


# ============== ROOT ENDPOINT ==============

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "security": "enabled"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
