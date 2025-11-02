"""
Main FastAPI Application

Entry point for the matching engine API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from ..matching_engine.config.database import init_db
from .config import settings
from .routers import orders_router, trades_router, market_router, websocket_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Matching Engine API...")
    
    # Initialize database
    try:
        init_db(database_url=settings.DATABASE_URL, echo=settings.DEBUG)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Matching Engine API...")


# Create FastAPI application
app = FastAPI(
    title="Cryptocurrency Matching Engine API",
    description="High-performance matching engine for cryptocurrency trading",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders_router)
app.include_router(trades_router)
app.include_router(market_router)
app.include_router(websocket_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": "Cryptocurrency Matching Engine API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns system health status.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected"
    }


@app.get("/api/v1/status", tags=["System"])
async def system_status():
    """
    Get system status and statistics.
    """
    from ..matching_engine.cache import cache_manager
    
    cache_stats = cache_manager.get_stats()
    
    return {
        "status": "operational",
        "version": "1.0.0",
        "uptime": "running",
        "endpoints": {
            "rest": "/api/v1",
            "websocket": "/ws",
            "docs": "/docs"
        },
        "cache": {
            "enabled": True,
            "size": cache_stats["size"],
            "hit_rate": f"{cache_stats['hit_rate']}%",
            "total_requests": cache_stats["total_requests"]
        }
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
