from fastapi import APIRouter

from app.api.common import NOT_FOUND, Limit, Offset, ResourceID
from app.core.database import SessionDep
from app.models import Membership
from app.schemas import MembershipCreate, MembershipPatch, MembershipRead
from app.services import memberships

router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.post("", response_model=MembershipRead, status_code=201, responses=NOT_FOUND)
async def create(data: MembershipCreate, session: SessionDep) -> Membership:
    return await memberships.create(session, data)


@router.get("", response_model=list[MembershipRead])
async def list_items(
    session: SessionDep,
    limit: Limit = 20,
    offset: Offset = 0,
) -> list[Membership]:
    return await memberships.list_memberships(session, limit, offset)


@router.get("/{id}", response_model=MembershipRead, responses=NOT_FOUND)
async def get(id: ResourceID, session: SessionDep) -> Membership:
    return await memberships.get(session, id)


@router.patch("/{id}", response_model=MembershipRead, responses=NOT_FOUND)
async def update(id: ResourceID, data: MembershipPatch, session: SessionDep) -> Membership:
    return await memberships.update(session, id, data)
