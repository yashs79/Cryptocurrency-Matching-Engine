"""
Database Configuration

Supports both SQLite (development) and PostgreSQL (production).
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()


class DatabaseConfig:
    """Database configuration"""
    
    def __init__(
        self,
        database_url: str = None,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_recycle: int = 3600,
        pool_timeout: int = 30
    ):
        """
        Initialize database configuration.
        
        Args:
            database_url: Database URL (defaults to SQLite in-memory)
            echo: Echo SQL statements
            pool_size: Connection pool size
            max_overflow: Max overflow connections
        """
        # Default to SQLite in-memory for development
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "sqlite:///./matching_engine.db"
            )
        
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.pool_timeout = pool_timeout
        
        # Create engine
        if database_url.startswith("sqlite"):
            # SQLite specific settings
            self.engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool if ":memory:" in database_url else None
            )
        else:
            # PostgreSQL settings with optimized pooling
            self.engine = create_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=pool_recycle,  # Recycle connections after 1 hour
                pool_timeout=pool_timeout,  # Wait 30s for connection
                connect_args={
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=30000"  # 30s query timeout
                }
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database configured: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """Return database URL with password masked"""
        url = self.database_url
        if "@" in url:
            # Mask password in URL
            parts = url.split("@")
            credentials = parts[0].split("://")[1]
            if ":" in credentials:
                user = credentials.split(":")[0]
                return url.replace(credentials, f"{user}:****")
        return url
    
    def create_tables(self):
        """Create all tables"""
        # Import models to register them with Base
        from ..models.order_model import OrderModel
        from ..models.trade_model import TradeModel
        
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """Drop all tables"""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def get_pool_stats(self) -> dict:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with pool stats
        """
        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow()
        }


# Global database config instance
_db_config: DatabaseConfig = None


def init_db(database_url: str = None, echo: bool = False) -> DatabaseConfig:
    """
    Initialize database.
    
    Args:
        database_url: Database URL
        echo: Echo SQL statements
        
    Returns:
        DatabaseConfig instance
    """
    global _db_config
    _db_config = DatabaseConfig(database_url=database_url, echo=echo)
    _db_config.create_tables()
    return _db_config


def get_session() -> Generator[Session, None, None]:
    """
    Get database session (for dependency injection).
    
    Yields:
        Database session
    """
    if _db_config is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    session = _db_config.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_config() -> DatabaseConfig:
    """Get the global database config"""
    if _db_config is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_config
