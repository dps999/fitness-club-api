from typing import Annotated

from fastapi import Path, Query

from app.schemas import MAX_INT, ErrorResponse

ResourceID = Annotated[int, Path(gt=0, le=MAX_INT)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=MAX_INT)]
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Resource not found"}}
CONFLICT = {409: {"model": ErrorResponse, "description": "Business rule conflict"}}
