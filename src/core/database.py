from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Column, DateTime, Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import settings

engine = create_async_engine(
    settings.ASYCNC_DATABASE_URL,
    #  echo=True,
    # connect_args={"ssl": None},
)


@asynccontextmanager
async def get_session():
    async with AsyncSession(engine) as session:
        yield session


class Database:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=True, future=True)

    async def connect(self):
        await self.engine.connect()

    async def disconnect(self):
        await self.engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, Any]:
        async with AsyncSession(self.engine) as session:
            yield session


class BaseModel(SQLModel):
    """Base model with common fields."""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=settings.get_now, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: None,
        sa_column=Column(DateTime(timezone=True), onupdate=settings.get_now),
    )
    is_deleted: bool = Field(default=False)
