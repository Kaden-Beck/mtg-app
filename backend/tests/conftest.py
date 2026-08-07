from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db import Base, get_db
from app.main import app

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://mtg:mtg@localhost:5432/mtg_test"
)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(TEST_DB_URL, echo=False, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as connection:
        trans = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()
            if trans.is_active:
                await trans.rollback()


@pytest_asyncio.fixture(loop_scope="session")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
