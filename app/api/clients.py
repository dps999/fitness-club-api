from fastapi import APIRouter

from app.api.common import CONFLICT, NOT_FOUND, Limit, Offset, ResourceID
from app.core.database import SessionDep
from app.models import Client
from app.schemas import ClientCreate, ClientPatch, ClientRead
from app.services import clients

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientRead, status_code=201, responses=CONFLICT)
async def create(data: ClientCreate, session: SessionDep) -> Client:
    return await clients.create(session, data)


@router.get("", response_model=list[ClientRead])
async def list_items(
    session: SessionDep,
    limit: Limit = 20,
    offset: Offset = 0,
) -> list[Client]:
    return await clients.list_clients(session, limit, offset)


@router.get("/{id}", response_model=ClientRead, responses=NOT_FOUND)
async def get(id: ResourceID, session: SessionDep) -> Client:
    return await clients.get(session, id)


@router.patch("/{id}", response_model=ClientRead, responses=NOT_FOUND | CONFLICT)
async def update(id: ResourceID, data: ClientPatch, session: SessionDep) -> Client:
    return await clients.update(session, id, data)


@router.delete("/{id}", status_code=204, responses=NOT_FOUND)
async def delete(id: ResourceID, session: SessionDep) -> None:
    await clients.delete(session, id)
