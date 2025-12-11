from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base, Client


class BusinessError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


async def get_or_404[Model: Base](
    session: AsyncSession,
    model: type[Model],
    object_id: int,
    label: str,
    *,
    for_update: bool = False,
) -> Model:
    obj = await session.get(model, object_id, with_for_update=for_update or None)
    if obj is None:
        raise BusinessError(404, f"{label} not found")
    return obj


async def list_page[Model: Base](
    session: AsyncSession, query: Select[tuple[Model]], limit: int, offset: int
) -> list[Model]:
    return list(await session.scalars(query.limit(limit).offset(offset)))


async def insert[Model: Base](session: AsyncSession, obj: Model) -> Model:
    session.add(obj)
    await session.flush()
    return obj


async def lock_client(session: AsyncSession, client_id: int) -> None:
    client = await session.scalar(
        select(Client.id).where(Client.id == client_id).with_for_update(read=True, key_share=True)
    )
    if client is None:
        raise BusinessError(404, "Client not found")
