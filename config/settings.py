"""
Application settings and configuration
"""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    ws_port: int = 8765
    metrics_port: int = 9090

    # Database
    database_url: str = "postgresql://matching:matching123@localhost:5432/matching_engine"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # Security
    secret_key: str = "change-me-in-production"
    api_key: Optional[str] = None

    # Performance
    max_workers: int = 4
    order_queue_size: int = 10000
    websocket_max_connections: int = 1000

    # Monitoring
    prometheus_enabled: bool = True
    metrics_namespace: str = "matching_engine"

    # Feature Flags
    enable_market_orders: bool = True
    enable_ioc_orders: bool = True
    enable_fok_orders: bool = True
    enable_stop_orders: bool = False

    # Rate Limiting
    rate_limit_orders_per_second: int = 100
    rate_limit_requests_per_minute: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
