from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def build_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
