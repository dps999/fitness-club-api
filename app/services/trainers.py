from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Trainer
from app.schemas import TrainerCreate
from app.services.common import get_or_404, insert, list_page


async def create(session: AsyncSession, data: TrainerCreate) -> Trainer:
    async with session.begin():
        return await insert(session, Trainer(**data.model_dump()))


async def list_trainers(session: AsyncSession, limit: int, offset: int) -> list[Trainer]:
    return await list_page(session, select(Trainer).order_by(Trainer.id), limit, offset)


async def get(session: AsyncSession, trainer_id: int) -> Trainer:
    return await get_or_404(session, Trainer, trainer_id, "Trainer")
