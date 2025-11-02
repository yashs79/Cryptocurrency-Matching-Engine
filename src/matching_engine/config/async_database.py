"""
Async Database Configuration

Async SQLAlchemy support for non-blocking database operations.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
import logging

logger = logging.getLogger(__name__)


class AsyncDatabaseConfig:
    """Async database configuration"""
    
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
        Initialize async database configuration.
        
        Args:
            database_url: Database URL (defaults to SQLite)
            echo: Echo SQL statements
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            pool_recycle: Connection recycle time
            pool_timeout: Pool timeout
        """
        # Default to SQLite for development
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "sqlite+aiosqlite:///./matching_engine.db"
            )
        
        # Convert sync URL to async if needed
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif database_url.startswith("sqlite://") and "aiosqlite" not in database_url:
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.pool_timeout = pool_timeout
        
        # Create async engine
        if database_url.startswith("sqlite"):
            # SQLite specific settings
            self.engine = create_async_engine(
                database_url,
                echo=echo,
                poolclass=NullPool if ":memory:" in database_url else None,
                connect_args={"check_same_thread": False} if "aiosqlite" in database_url else {}
            )
        else:
            # PostgreSQL settings with optimized pooling
            self.engine = create_async_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
                pool_recycle=pool_recycle,
                pool_timeout=pool_timeout,
                poolclass=AsyncAdaptedQueuePool
            )
        
        # Create async session factory
        self.AsyncSessionLocal = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        logger.info(f"Async database configured: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """Return database URL with password masked"""
        url = self.database_url
        if "@" in url:
            parts = url.split("@")
            credentials = parts[0].split("://")[1]
            if ":" in credentials:
                user = credentials.split(":")[0]
                return url.replace(credentials, f"{user}:****")
        return url
    
    async def create_tables(self):
        """Create all tables asynchronously"""
        from ..config.database import Base
        from ..models.order_model import OrderModel
        from ..models.trade_model import TradeModel
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Async database tables created")
    
    async def drop_tables(self):
        """Drop all tables asynchronously"""
        from ..config.database import Base
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Async database tables dropped")
    
    def get_session(self) -> AsyncSession:
        """Get a new async database session"""
        return self.AsyncSessionLocal()
    
    async def close(self):
        """Close the async engine"""
        await self.engine.dispose()
        logger.info("Async database engine closed")


# Global async database config instance
_async_db_config: AsyncDatabaseConfig = None


async def init_async_db(database_url: str = None, echo: bool = False) -> AsyncDatabaseConfig:
    """
    Initialize async database.
    
    Args:
        database_url: Database URL
        echo: Echo SQL statements
        
    Returns:
        AsyncDatabaseConfig instance
    """
    global _async_db_config
    _async_db_config = AsyncDatabaseConfig(database_url=database_url, echo=echo)
    await _async_db_config.create_tables()
    return _async_db_config


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session (for dependency injection).
    
    Yields:
        Async database session
    """
    if _async_db_config is None:
        raise RuntimeError("Async database not initialized. Call init_async_db() first.")
    
    async with _async_db_config.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_async_db_config() -> AsyncDatabaseConfig:
    """Get the global async database config"""
    if _async_db_config is None:
        raise RuntimeError("Async database not initialized. Call init_async_db() first.")
    return _async_db_config
