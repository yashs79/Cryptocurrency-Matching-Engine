"""
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from prometheus_client import make_asgi_app

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Cryptocurrency Matching Engine API",
        version="1.0.0",
        description="""
## 🚀 High-Performance Cryptocurrency Matching Engine

A production-ready matching engine implementing price-time priority algorithm with microsecond-level latency targets.

### Features
* **Price-Time Priority Matching** - Fair order execution following industry standards
* **Multiple Order Types** - Market, Limit, IOC, FOK orders
* **Real-time Market Data** - WebSocket streaming for order book updates
* **High Performance** - Optimized for low-latency order processing
* **RESTful API** - Complete REST API for order management
* **WebSocket API** - Real-time market data and trade execution streams

### Order Types Supported
* **Market Orders** - Execute immediately at best available price
* **Limit Orders** - Execute at specified price or better
* **IOC (Immediate-Or-Cancel)** - Execute immediately, cancel remainder
* **FOK (Fill-Or-Kill)** - Execute completely or cancel entirely

### Performance Targets
* **Throughput**: 1,000-5,000 orders/sec
* **Matching Latency**: P99 < 10ms
* **API Response Time**: P99 < 100ms
* **WebSocket Latency**: < 50ms

### Contact & Support
* **GitHub**: [Matching Engine Repository](https://github.com/your-org/matching-engine)
* **Documentation**: [Full Documentation](https://docs.matching-engine.com)
        """,
        routes=app.routes,
        contact={
            "name": "Matching Engine Team",
            "email": "support@matching-engine.com",
            "url": "https://github.com/your-org/matching-engine"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Local Development"
            },
            {
                "url": "https://dev.matching-engine.com",
                "description": "Development Environment"
            },
            {
                "url": "https://staging.matching-engine.com",
                "description": "Staging Environment"
            },
            {
                "url": "https://api.matching-engine.com",
                "description": "Production Environment"
            }
        ],
        tags=[
            {
                "name": "health",
                "description": "Health check and system status endpoints"
            },
            {
                "name": "orders",
                "description": "Order submission and management"
            },
            {
                "name": "orderbook",
                "description": "Order book data and market depth"
            },
            {
                "name": "trades",
                "description": "Trade execution history"
            },
            {
                "name": "websocket",
                "description": "Real-time WebSocket streams"
            }
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token authentication"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="Cryptocurrency Matching Engine API",
    description="High-performance matching engine for cryptocurrency trading",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    terms_of_service="https://matching-engine.com/terms",
    contact={
        "name": "Matching Engine Team",
        "email": "support@matching-engine.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Set custom OpenAPI schema
app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get(
    "/",
    tags=["health"],
    summary="Root Endpoint",
    description="Returns basic service information and status",
    response_description="Service information"
)
async def root():
    """
    ## Root Endpoint
    
    Returns basic information about the matching engine service.
    
    **Returns:**
    - `service`: Service name
    - `version`: Current version
    - `status`: Operational status
    - `docs`: Link to API documentation
    - `health`: Link to health check endpoint
    """
    return {
        "service": "Cryptocurrency Matching Engine",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "openapi": "/openapi.json"
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Health Check",
    description="Check if the service is healthy and operational",
    response_description="Health status"
)
async def health_check():
    """
    ## Health Check Endpoint
    
    Returns the current health status of the matching engine.
    
    **Returns:**
    - `status`: Health status (healthy/unhealthy)
    - `service`: Service name
    - `version`: Current version
    - `uptime`: Service uptime (future implementation)
    - `checks`: Individual component health checks (future implementation)
    
    **Status Codes:**
    - `200`: Service is healthy
    - `503`: Service is unhealthy
    """
    return {
        "status": "healthy",
        "service": "matching-engine",
        "version": "1.0.0",
        "environment": "development",
        "components": {
            "api": "healthy",
            "database": "not_configured",
            "redis": "not_configured",
            "websocket": "not_configured"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
