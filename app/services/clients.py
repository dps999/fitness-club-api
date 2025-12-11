from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client
from app.schemas import ClientCreate, ClientPatch
from app.services.common import get_or_404, insert, list_page


async def create(session: AsyncSession, data: ClientCreate) -> Client:
    async with session.begin():
        return await insert(session, Client(**data.model_dump()))


async def list_clients(session: AsyncSession, limit: int, offset: int) -> list[Client]:
    return await list_page(session, select(Client).order_by(Client.id), limit, offset)


async def get(session: AsyncSession, client_id: int) -> Client:
    return await get_or_404(session, Client, client_id, "Client")


async def update(session: AsyncSession, client_id: int, data: ClientPatch) -> Client:
    async with session.begin():
        client = await get_or_404(session, Client, client_id, "Client", for_update=True)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(client, field, value)
        return client


async def delete(session: AsyncSession, client_id: int) -> None:
    async with session.begin():
        client = await get_or_404(session, Client, client_id, "Client", for_update=True)
        await session.delete(client)
