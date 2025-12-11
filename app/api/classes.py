from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.common import CONFLICT, NOT_FOUND, Limit, Offset, ResourceID
from app.core.database import SessionDep
from app.models import FitnessClass
from app.schemas import MAX_INT, ClassCreate, ClassPatch, ClassRead
from app.services import classes

router = APIRouter(prefix="/classes", tags=["classes"])


@router.post("", response_model=ClassRead, status_code=201, responses=NOT_FOUND)
async def create(data: ClassCreate, session: SessionDep) -> FitnessClass:
    return await classes.create(session, data)


@router.get("", response_model=list[ClassRead])
async def list_items(
    session: SessionDep,
    limit: Limit = 20,
    offset: Offset = 0,
    class_date: Annotated[date | None, Query(alias="date", description="Class date in UTC")] = None,
    trainer_id: Annotated[int | None, Query(gt=0, le=MAX_INT)] = None,
) -> list[FitnessClass]:
    return await classes.list_classes(session, limit, offset, class_date, trainer_id)


@router.get("/{id}", response_model=ClassRead, responses=NOT_FOUND)
async def get(id: ResourceID, session: SessionDep) -> FitnessClass:
    return await classes.get(session, id)


@router.patch("/{id}", response_model=ClassRead, responses=NOT_FOUND | CONFLICT)
async def update(id: ResourceID, data: ClassPatch, session: SessionDep) -> FitnessClass:
    return await classes.update(session, id, data)


@router.delete("/{id}", status_code=204, responses=NOT_FOUND)
async def delete(id: ResourceID, session: SessionDep) -> None:
    await classes.delete(session, id)
