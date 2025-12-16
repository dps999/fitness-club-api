import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.database import make_engine


async def create_class(
    api: AsyncClient, capacity: int = 1, *, starts_at: datetime | None = None
) -> dict:
    trainer = await api.post("trainers", json={"name": "Alex", "specialization": "Strength"})
    response = await api.post(
        "classes",
        json={
            "title": "Strength",
            "trainer_id": trainer.json()["id"],
            "starts_at": (starts_at or datetime.now(UTC) + timedelta(days=7)).isoformat(),
            "duration_minutes": 60,
            "capacity": capacity,
        },
    )
    assert response.status_code == 201
    return response.json()


async def create_client(
    api: AsyncClient,
    email: str,
    fitness_class: dict,
    *,
    membership_days: tuple[int, int] | None = (0, 0),
    status: str = "active",
) -> int:
    client = await api.post(
        "clients",
        json={"first_name": "Sam", "last_name": "Lee", "phone": "+35712345678", "email": email},
    )
    client_id = client.json()["id"]
    if membership_days is not None:
        class_date = datetime.fromisoformat(fitness_class["starts_at"]).date()
        start, end = (class_date + timedelta(days=days) for days in membership_days)
        response = await api.post(
            "memberships",
            json={
                "client_id": client_id,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "status": status,
            },
        )
        assert response.status_code == 201
    return client_id


async def test_successful_booking_on_membership_boundary(api: AsyncClient) -> None:
    fitness_class = await create_class(api)
    client_id = await create_client(api, "sam@example.com", fitness_class)
    data = {"client_id": client_id, "class_id": fitness_class["id"]}
    response = await api.post("bookings", json=data)
    assert response.status_code == 201
    assert response.json() | data == response.json()
    assert (await api.get("bookings")).json() == [response.json()]


async def test_duplicate_booking(api: AsyncClient) -> None:
    fitness_class = await create_class(api, capacity=2)
    client_id = await create_client(api, "sam@example.com", fitness_class)
    data = {"client_id": client_id, "class_id": fitness_class["id"]}
    assert (await api.post("bookings", json=data)).status_code == 201
    duplicate = await api.post("bookings", json=data)
    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "The client is already booked for this class"}


@pytest.mark.parametrize(
    ("membership_days", "status"),
    [
        (None, "active"),
        ((-7, -1), "active"),
        ((1, 7), "active"),
        ((-1, 1), "expired"),
        ((-1, 1), "cancelled"),
    ],
    ids=["absent", "ended-before-class", "starts-after-class", "expired", "cancelled"],
)
async def test_booking_requires_valid_membership(
    api: AsyncClient, membership_days: tuple[int, int] | None, status: str
) -> None:
    fitness_class = await create_class(api)
    client_id = await create_client(
        api, "sam@example.com", fitness_class, membership_days=membership_days, status=status
    )
    response = await api.post(
        "bookings", json={"client_id": client_id, "class_id": fitness_class["id"]}
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "An active membership covering the class date is required"}


async def test_booking_requires_existing_client_and_class(api: AsyncClient) -> None:
    fitness_class = await create_class(api)
    client_id = await create_client(api, "sam@example.com", fitness_class)
    missing_client = await api.post(
        "bookings", json={"client_id": 999, "class_id": fitness_class["id"]}
    )
    missing_class = await api.post("bookings", json={"client_id": client_id, "class_id": 999})
    assert missing_client.status_code == 404
    assert missing_client.json() == {"detail": "Client not found"}
    assert missing_class.status_code == 404
    assert missing_class.json() == {"detail": "Class not found"}


async def test_cannot_book_a_past_class(api: AsyncClient) -> None:
    fitness_class = await create_class(api, starts_at=datetime.now(UTC) - timedelta(hours=1))
    client_id = await create_client(api, "sam@example.com", fitness_class)
    response = await api.post(
        "bookings", json={"client_id": client_id, "class_id": fitness_class["id"]}
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "The class has already started"}


async def test_full_class_cancellation_and_reuse(api: AsyncClient) -> None:
    fitness_class = await create_class(api)
    first = await create_client(api, "first@example.com", fitness_class)
    second = await create_client(api, "second@example.com", fitness_class)
    first_booking = await api.post(
        "bookings", json={"client_id": first, "class_id": fitness_class["id"]}
    )
    assert first_booking.status_code == 201
    second_booking = {"client_id": second, "class_id": fitness_class["id"]}
    rejected = await api.post("bookings", json=second_booking)
    assert rejected.status_code == 409
    assert rejected.json() == {"detail": "The class is full"}

    path = f"bookings/{first_booking.json()['id']}"
    assert (await api.delete(path)).status_code == 204
    assert (await api.delete(path)).status_code == 404
    assert (await api.get("bookings")).json() == []
    accepted = await api.post("bookings", json=second_booking)
    assert accepted.status_code == 201
    assert (await api.get("bookings")).json() == [accepted.json()]


async def test_capacity_cannot_drop_below_active_booking_count(api: AsyncClient) -> None:
    fitness_class = await create_class(api, capacity=2)
    class_id = fitness_class["id"]
    for email in ("first@example.com", "second@example.com"):
        client_id = await create_client(api, email, fitness_class)
        response = await api.post("bookings", json={"client_id": client_id, "class_id": class_id})
        assert response.status_code == 201
    response = await api.patch(f"classes/{class_id}", json={"capacity": 1})
    assert response.status_code == 409
    assert (await api.get(f"classes/{class_id}")).json()["capacity"] == 2


async def test_concurrent_requests_for_last_seat(api: AsyncClient, test_database_url: str) -> None:
    fitness_class = await create_class(api, capacity=2)
    class_id = fitness_class["id"]
    existing = await create_client(api, "existing@example.com", fitness_class)
    assert (
        await api.post("bookings", json={"client_id": existing, "class_id": class_id})
    ).status_code == 201
    contenders = [
        await create_client(api, "first@example.com", fitness_class),
        await create_client(api, "second@example.com", fitness_class),
    ]

    engine = make_engine(test_database_url)
    try:
        async with asyncio.timeout(10), asyncio.TaskGroup() as group, engine.begin() as lock:
            # Hold the row until both HTTP requests are waiting for it inside PostgreSQL.
            await lock.execute(
                text("SELECT id FROM classes WHERE id = :class_id FOR UPDATE"),
                {"class_id": class_id},
            )
            tasks = [
                group.create_task(
                    api.post("bookings", json={"client_id": client, "class_id": class_id})
                )
                for client in contenders
            ]
            async with engine.connect() as monitor:
                await monitor.execution_options(isolation_level="AUTOCOMMIT")
                waiting = text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock' "
                    "AND query LIKE '%FROM classes%FOR UPDATE%'"
                )
                while await monitor.scalar(waiting) != 2:
                    await asyncio.sleep(0.02)
    finally:
        await engine.dispose()

    responses = [task.result() for task in tasks]
    assert sorted(response.status_code for response in responses) == [201, 409]
    rejected = next(response for response in responses if response.status_code == 409)
    assert rejected.json() == {"detail": "The class is full"}
    bookings = (await api.get("bookings")).json()
    assert {booking["client_id"] for booking in bookings} == {
        existing,
        next(response.json()["client_id"] for response in responses if response.status_code == 201),
    }
    assert len(bookings) == fitness_class["capacity"]


@pytest.mark.parametrize("resource", ["clients", "classes"])
async def test_deleting_client_or_class_removes_bookings(api: AsyncClient, resource: str) -> None:
    fitness_class = await create_class(api)
    class_id = fitness_class["id"]
    client_id = await create_client(api, "sam@example.com", fitness_class)
    created = await api.post("bookings", json={"client_id": client_id, "class_id": class_id})
    assert created.status_code == 201

    target_id = client_id if resource == "clients" else class_id
    assert (await api.delete(f"{resource}/{target_id}")).status_code == 204
    assert (await api.get("bookings")).json() == []
    if resource == "clients":
        assert (await api.get("memberships")).json() == []
