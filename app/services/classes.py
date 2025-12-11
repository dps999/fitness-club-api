from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, FitnessClass
from app.schemas import ClassCreate, ClassPatch
from app.services import trainers
from app.services.common import BusinessError, get_or_404, insert, list_page


async def create(session: AsyncSession, data: ClassCreate) -> FitnessClass:
    async with session.begin():
        await trainers.get(session, data.trainer_id)
        return await insert(session, FitnessClass(**data.model_dump()))


async def list_classes(
    session: AsyncSession, limit: int, offset: int, class_date: date | None, trainer_id: int | None
) -> list[FitnessClass]:
    query = select(FitnessClass).order_by(FitnessClass.starts_at, FitnessClass.id)
    if class_date is not None:
        query = query.where(
            FitnessClass.starts_at >= datetime.combine(class_date, time.min, UTC),
            FitnessClass.starts_at <= datetime.combine(class_date, time.max, UTC),
        )
    if trainer_id is not None:
        query = query.where(FitnessClass.trainer_id == trainer_id)
    return await list_page(session, query, limit, offset)


async def get(session: AsyncSession, class_id: int, *, for_update: bool = False) -> FitnessClass:
    return await get_or_404(session, FitnessClass, class_id, "Class", for_update=for_update)


async def count_bookings(session: AsyncSession, class_id: int) -> int:
    query = select(func.count()).select_from(Booking).where(Booking.class_id == class_id)
    return (await session.execute(query)).scalar_one()


async def update(session: AsyncSession, class_id: int, data: ClassPatch) -> FitnessClass:
    async with session.begin():
        fitness_class = await get(session, class_id, for_update=True)
        if data.trainer_id is not None:
            await trainers.get(session, data.trainer_id)
        if data.capacity is not None and data.capacity < fitness_class.capacity:
            if data.capacity < await count_bookings(session, class_id):
                raise BusinessError(409, "Capacity cannot be lower than the current booking count")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(fitness_class, field, value)
        return fitness_class


async def delete(session: AsyncSession, class_id: int) -> None:
    async with session.begin():
        await session.delete(await get(session, class_id, for_update=True))
