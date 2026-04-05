"""Database engine and session factory configuration.

Provides factory functions for creating async SQLAlchemy engines and
session makers with connection pooling.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_recycle: int = 3600,
) -> AsyncEngine:
    """Create an async SQLAlchemy engine with connection pooling.

    Args:
        database_url: The database connection URL.
        pool_size: Number of persistent connections in the pool.
        max_overflow: Maximum overflow connections beyond pool_size.
        pool_recycle: Seconds after which connections are recycled.

    Returns:
        A configured async SQLAlchemy engine.
    """
    return create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=pool_recycle,
    )


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the given engine.

    Args:
        engine: The async SQLAlchemy engine.

    Returns:
        An async session maker configured with expire_on_commit=False.
    """
    return async_sessionmaker(engine, expire_on_commit=False)
