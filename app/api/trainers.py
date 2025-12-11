from fastapi import APIRouter

from app.api.common import NOT_FOUND, Limit, Offset, ResourceID
from app.core.database import SessionDep
from app.models import Trainer
from app.schemas import TrainerCreate, TrainerRead
from app.services import trainers

router = APIRouter(prefix="/trainers", tags=["trainers"])


@router.post("", response_model=TrainerRead, status_code=201)
async def create(data: TrainerCreate, session: SessionDep) -> Trainer:
    return await trainers.create(session, data)


@router.get("", response_model=list[TrainerRead])
async def list_items(
    session: SessionDep,
    limit: Limit = 20,
    offset: Offset = 0,
) -> list[Trainer]:
    return await trainers.list_trainers(session, limit, offset)


@router.get("/{id}", response_model=TrainerRead, responses=NOT_FOUND)
async def get(id: ResourceID, session: SessionDep) -> Trainer:
    return await trainers.get(session, id)
