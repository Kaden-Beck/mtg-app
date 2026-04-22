from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://mtg@localhost:5432/mtg")


AsyncSessionLocal = async_sessionmaker(
    engine=create_async_engine(DATABASE_URL, echo=False),
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
