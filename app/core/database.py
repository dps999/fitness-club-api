from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.core.config import get_settings


def make_engine(url: str | None = None) -> AsyncEngine:
    return create_async_engine(
        url or str(get_settings().database_url),
        isolation_level="READ COMMITTED",
        pool_pre_ping=True,
        connect_args={"server_settings": {"timezone": "UTC"}},
    )


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
