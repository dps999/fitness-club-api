"""Create fitness club tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_clients_email"),
    )
    op.create_table(
        "trainers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("specialization", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("trainer_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.CheckConstraint("capacity > 0", name="ck_classes_capacity"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_classes_duration"),
        sa.ForeignKeyConstraint(["trainer_id"], ["trainers.id"], name="fk_classes_trainer"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_classes_starts_at", "classes", ["starts_at"], unique=False)
    op.create_index(
        "ix_classes_trainer_starts_at", "classes", ["trainer_id", "starts_at"], unique=False
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "expired",
                "cancelled",
                name="ck_memberships_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.CheckConstraint("start_date <= end_date", name="ck_memberships_date_order"),
        sa.ForeignKeyConstraint(
            ["client_id"], ["clients.id"], name="fk_memberships_client", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_memberships_client_dates",
        "memberships",
        ["client_id", "start_date", "end_date"],
        unique=False,
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["class_id"], ["classes.id"], name="fk_bookings_class", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["clients.id"], name="fk_bookings_client", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_id", "client_id", name="uq_bookings_class_client"),
    )
    op.create_index("ix_bookings_client_id", "bookings", ["client_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_bookings_client_id", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("ix_memberships_client_dates", table_name="memberships")
    op.drop_table("memberships")
    op.drop_index("ix_classes_trainer_starts_at", table_name="classes")
    op.drop_index("ix_classes_starts_at", table_name="classes")
    op.drop_table("classes")
    op.drop_table("trainers")
    op.drop_table("clients")
