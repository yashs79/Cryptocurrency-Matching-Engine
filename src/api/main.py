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
    logger.info("Starting up...")
    
    # Initialize database
    database_url = os.getenv("DATABASE_URL", "sqlite:///./matching_engine.db")
    init_db(database_url=database_url, echo=False)
    logger.info("Database initialized")
    
    # Start background tasks
    from ..matching_engine.utils.background_tasks import (
        background_task_manager,
        cache_cleanup_task,
        connection_pool_monitor,
        event_queue_monitor
    )
    from ..matching_engine.events.async_event_publisher import async_event_publisher
    
    await background_task_manager.start()
    
    # Schedule periodic tasks
    background_task_manager.schedule_periodic(
        "cache_cleanup",
        cache_cleanup_task,
        interval_seconds=300,  # Every 5 minutes
        run_immediately=False
    )
    
    background_task_manager.schedule_periodic(
        "pool_monitor",
        connection_pool_monitor,
        interval_seconds=60,  # Every minute
        run_immediately=False
    )
    
    background_task_manager.schedule_periodic(
        "event_monitor",
        event_queue_monitor,
        interval_seconds=30,  # Every 30 seconds
        run_immediately=False
    )
    
    # Start async event processing
    await async_event_publisher.start_processing()
    
    logger.info("Background tasks started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Stop background tasks
    await async_event_publisher.stop_processing()
    await background_task_manager.stop()
    
    logger.info("Cleanup complete")


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
    from ..matching_engine.config.database import get_db_config
    from ..matching_engine.utils.background_tasks import background_task_manager
    from ..matching_engine.events.async_event_publisher import async_event_publisher
    
    cache_stats = cache_manager.get_stats()
    
    # Get database pool stats
    try:
        db_config = get_db_config()
        pool_stats = db_config.get_pool_stats()
    except:
        pool_stats = {"error": "Database not initialized"}
    
    # Get background task stats
    task_stats = background_task_manager.get_stats()
    event_stats = async_event_publisher.get_stats()
    
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
        },
        "database": {
            "pool_size": pool_stats.get("size", 0),
            "active_connections": pool_stats.get("checked_out", 0),
            "idle_connections": pool_stats.get("checked_in", 0),
            "total_connections": pool_stats.get("total_connections", 0)
        },
        "background_tasks": {
            "running": task_stats["running"],
            "active_tasks": task_stats["active_tasks"],
            "completed": task_stats["completed"],
            "failed": task_stats["failed"]
        },
        "events": {
            "published": event_stats["published"],
            "processed": event_stats["processed"],
            "queue_size": event_stats["queue_size"],
            "running": event_stats["running"]
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
