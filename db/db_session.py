import os
from typing import Generator
import aioredis

from sqlalchemy.engine import url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import REDIS_HOST, REDIS_PORT

ASYNC_DATABASE_URL = url.URL.create(
    drivername="postgresql+asyncpg",
    database=os.getenv("POSTGRES_DB", "postgres"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)

engine = create_async_engine(ASYNC_DATABASE_URL, future=True)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> Generator:
    """Dependency for getting async session"""
    async with async_session() as session:
        yield session


redis = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
