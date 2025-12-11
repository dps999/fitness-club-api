from datetime import UTC, datetime

from sqlalchemy import delete as delete_row
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking
from app.schemas import BookingCreate
from app.services import classes, memberships
from app.services.common import BusinessError, insert, list_page, lock_client


async def create(session: AsyncSession, data: BookingCreate) -> Booking:
    async with session.begin():
        fitness_class = await classes.get(session, data.class_id, for_update=True)
        await lock_client(session, data.client_id)
        if fitness_class.starts_at <= datetime.now(UTC):
            raise BusinessError(409, "The class has already started")

        class_date = fitness_class.starts_at.astimezone(UTC).date()
        if not await memberships.has_valid_membership(session, data.client_id, class_date):
            raise BusinessError(409, "An active membership covering the class date is required")

        existing = await session.scalar(
            select(Booking.id).where(
                Booking.class_id == data.class_id, Booking.client_id == data.client_id
            )
        )
        if existing is not None:
            raise BusinessError(409, "The client is already booked for this class")
        if await classes.count_bookings(session, data.class_id) >= fitness_class.capacity:
            raise BusinessError(409, "The class is full")
        return await insert(session, Booking(**data.model_dump()))


async def list_bookings(session: AsyncSession, limit: int, offset: int) -> list[Booking]:
    return await list_page(session, select(Booking).order_by(Booking.id), limit, offset)


async def delete(session: AsyncSession, booking_id: int) -> None:
    async with session.begin():
        class_id = await session.scalar(select(Booking.class_id).where(Booking.id == booking_id))
        if class_id is None:
            raise BusinessError(404, "Booking not found")
        await classes.get(session, class_id, for_update=True)
        deleted_id = await session.scalar(
            delete_row(Booking).where(Booking.id == booking_id).returning(Booking.id)
        )
        if deleted_id is None:
            raise BusinessError(404, "Booking not found")
