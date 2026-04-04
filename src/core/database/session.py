# File: src/core/database/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .models import Base

# ADR 004: Using SQLite for the Modular Monolith
DATABASE_URL = "sqlite+aiosqlite:///./superchat.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def init_db():
    """Creates all tables in the SQLite database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """FastAPI dependency to get a database session."""
    async with AsyncSessionLocal() as session:
        yield session
