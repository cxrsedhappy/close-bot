from __future__ import annotations

import contextlib

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///db/database?check_same_thread=False', echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def global_init():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@contextlib.asynccontextmanager
async def create_session() -> AsyncSession:
    async with session_factory() as session:
        yield session
