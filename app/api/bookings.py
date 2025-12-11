from fastapi import APIRouter

from app.api.common import CONFLICT, NOT_FOUND, Limit, Offset, ResourceID
from app.core.database import SessionDep
from app.models import Booking
from app.schemas import BookingCreate, BookingRead
from app.services import bookings

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=201, responses=NOT_FOUND | CONFLICT)
async def create(data: BookingCreate, session: SessionDep) -> Booking:
    return await bookings.create(session, data)


@router.get("", response_model=list[BookingRead])
async def list_items(
    session: SessionDep,
    limit: Limit = 20,
    offset: Offset = 0,
) -> list[Booking]:
    return await bookings.list_bookings(session, limit, offset)


@router.delete("/{id}", status_code=204, responses=NOT_FOUND)
async def delete(id: ResourceID, session: SessionDep) -> None:
    await bookings.delete(session, id)
