import os
from typing import Generator

from redis import asyncio as aioredis
from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

Base = declarative_base(metadata=MetaData())

# Postgresql
SYNC_DATABASE_URL = url.URL.create(
    drivername="postgresql+psycopg2",
    database=os.getenv("POSTGRES_DB", "postgres"),
    port=int(os.getenv("POSTGRES_PORT", "5335")),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)


ASYNC_DATABASE_URL = url.URL.create(
    drivername="postgresql+asyncpg",
    database=os.getenv("POSTGRES_DB", "postgres"),
    port=int(os.getenv("POSTGRES_PORT", "5335")),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)

async_engine = create_async_engine(ASYNC_DATABASE_URL, future=True)
async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

sync_engine = create_engine(SYNC_DATABASE_URL)
sync_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=sync_engine))


async def get_session() -> Generator:
    """Dependency for getting async session"""
    async with async_session() as session:
        yield session


# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
