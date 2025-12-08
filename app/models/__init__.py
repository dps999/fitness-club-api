from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MembershipStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("email", name="uq_clients_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254))
    phone: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_memberships_date_order"),
        Index("ix_memberships_client_dates", "client_id", "start_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", name="fk_memberships_client", ondelete="CASCADE")
    )
    start_date: Mapped[date]
    end_date: Mapped[date]
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(
            MembershipStatus,
            name="ck_memberships_status",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda statuses: [status.value for status in statuses],
            length=9,
        )
    )


class Trainer(Base):
    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    specialization: Mapped[str] = mapped_column(String(100))


class FitnessClass(Base):
    __tablename__ = "classes"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_classes_capacity"),
        CheckConstraint("duration_minutes > 0", name="ck_classes_duration"),
        Index("ix_classes_starts_at", "starts_at"),
        Index("ix_classes_trainer_starts_at", "trainer_id", "starts_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    trainer_id: Mapped[int] = mapped_column(ForeignKey("trainers.id", name="fk_classes_trainer"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int]
    capacity: Mapped[int]


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("class_id", "client_id", name="uq_bookings_class_client"),
        Index("ix_bookings_client_id", "client_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", name="fk_bookings_client", ondelete="CASCADE")
    )
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", name="fk_bookings_class", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
