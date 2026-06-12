from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from app.utils.settings import secrets as s


def build_db_url() -> str:
    return (
        f"postgresql+psycopg://{s.postgres_user}:{s.postgres_password}"
        f"@{s.db_host}:{s.db_port_container}/{s.postgres_db}"
    )


async def create_engine() -> AsyncEngine:
    engine = create_async_engine(
        build_db_url(),
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    return engine


async def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )