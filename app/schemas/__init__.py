from datetime import UTC, date, datetime
from typing import Annotated, Any, Self

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)

from app.models import MembershipStatus

MAX_INT = 2_147_483_647
PositiveInt = Annotated[int, Field(strict=True, gt=0, le=MAX_INT)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
Phone = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=32, pattern=r"^\+?[0-9][0-9 ()-]{5,31}$"),
]


def normalize_email(value: str) -> str:
    normalized = value.lower()
    if len(normalized) > 254:
        raise ValueError("Email cannot exceed 254 characters")
    return normalized


def as_utc(value: datetime) -> datetime:
    try:
        return value.astimezone(UTC)
    except OverflowError as exc:
        raise ValueError("Timestamp is outside the supported UTC range") from exc


Email = Annotated[EmailStr, AfterValidator(normalize_email)]
UtcDatetime = Annotated[AwareDatetime, AfterValidator(as_utc)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Patch(Input):
    @model_validator(mode="before")
    @classmethod
    def reject_null_fields(cls, value: Any) -> Any:
        if isinstance(value, dict) and any(field is None for field in value.values()):
            raise ValueError("Omit fields you do not want to update. Null values are not allowed.")
        return value


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ClientCreate(Input):
    first_name: Name
    last_name: Name
    email: Email
    phone: Phone


class ClientPatch(Patch):
    first_name: Name | None = None
    last_name: Name | None = None
    email: Email | None = None
    phone: Phone | None = None


class ClientRead(ORMResponse):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    created_at: datetime


class MembershipCreate(Input):
    client_id: PositiveInt
    start_date: date
    end_date: date
    status: MembershipStatus = MembershipStatus.ACTIVE

    @model_validator(mode="after")
    def check_date_order(self) -> Self:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self


class MembershipPatch(Patch):
    start_date: date | None = None
    end_date: date | None = None
    status: MembershipStatus | None = None


class MembershipRead(ORMResponse):
    id: int
    client_id: int
    start_date: date
    end_date: date
    status: MembershipStatus


class TrainerCreate(Input):
    name: Name
    specialization: Name


class TrainerRead(ORMResponse):
    id: int
    name: str
    specialization: str


class ClassCreate(Input):
    title: Title
    trainer_id: PositiveInt
    starts_at: UtcDatetime
    duration_minutes: PositiveInt
    capacity: PositiveInt


class ClassPatch(Patch):
    title: Title | None = None
    trainer_id: PositiveInt | None = None
    starts_at: UtcDatetime | None = None
    duration_minutes: PositiveInt | None = None
    capacity: PositiveInt | None = None


class ClassRead(ORMResponse):
    id: int
    title: str
    trainer_id: int
    starts_at: datetime
    duration_minutes: int
    capacity: int


class BookingCreate(Input):
    client_id: PositiveInt
    class_id: PositiveInt


class BookingRead(ORMResponse):
    id: int
    client_id: int
    class_id: int
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
