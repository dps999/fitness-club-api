from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, MembershipStatus
from app.schemas import MembershipCreate, MembershipPatch
from app.services.common import BusinessError, get_or_404, insert, list_page, lock_client


async def create(session: AsyncSession, data: MembershipCreate) -> Membership:
    async with session.begin():
        await lock_client(session, data.client_id)
        return await insert(session, Membership(**data.model_dump()))


async def list_memberships(session: AsyncSession, limit: int, offset: int) -> list[Membership]:
    return await list_page(session, select(Membership).order_by(Membership.id), limit, offset)


async def get(session: AsyncSession, membership_id: int) -> Membership:
    return await get_or_404(session, Membership, membership_id, "Membership")


async def update(session: AsyncSession, membership_id: int, data: MembershipPatch) -> Membership:
    async with session.begin():
        membership = await get_or_404(
            session, Membership, membership_id, "Membership", for_update=True
        )
        changes = data.model_dump(exclude_unset=True)
        start_date = changes.get("start_date", membership.start_date)
        end_date = changes.get("end_date", membership.end_date)
        if start_date > end_date:
            raise BusinessError(422, "start_date must be on or before end_date")
        for field, value in changes.items():
            setattr(membership, field, value)
        return membership


async def has_valid_membership(session: AsyncSession, client_id: int, class_date: date) -> bool:
    query = (
        select(Membership.id)
        .where(
            Membership.client_id == client_id,
            Membership.status == MembershipStatus.ACTIVE,
            Membership.start_date <= class_date,
            Membership.end_date >= class_date,
        )
        .order_by(Membership.id)
        .limit(1)
        .with_for_update(read=True)
    )
    return await session.scalar(query) is not None
