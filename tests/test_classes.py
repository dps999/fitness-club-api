from httpx import AsyncClient

TRAINER = {"name": "Alex Morgan", "specialization": "Mobility"}
CLASS = {
    "title": "Mobility",
    "starts_at": "2030-05-01T01:30:00+03:00",
    "duration_minutes": 45,
    "capacity": 8,
}


async def test_create_class_with_timezone(api: AsyncClient) -> None:
    trainer = await api.post("trainers", json=TRAINER)
    assert trainer.status_code == 201
    trainer_id = trainer.json()["id"]
    assert (await api.get(f"trainers/{trainer_id}")).json() == trainer.json()
    assert (await api.get("trainers")).json() == [trainer.json()]

    response = await api.post("classes", json=CLASS | {"trainer_id": trainer_id})
    assert response.status_code == 201
    class_id = response.json()["id"]
    assert response.json() == CLASS | {
        "id": class_id,
        "trainer_id": trainer_id,
        "starts_at": "2030-04-30T22:30:00Z",
    }
    assert (await api.get(f"classes/{class_id}")).json() == response.json()


async def test_class_validation(api: AsyncClient) -> None:
    trainer = await api.post("trainers", json=TRAINER)
    data = CLASS | {"trainer_id": trainer.json()["id"]}
    assert (await api.post("classes", json=data | {"capacity": 0})).status_code == 422
    naive_time = data | {"starts_at": "2030-05-01T01:30:00"}
    assert (await api.post("classes", json=naive_time)).status_code == 422
    assert (await api.post("classes", json=data | {"trainer_id": 999})).status_code == 404


async def test_class_filters_pagination_update_and_delete(api: AsyncClient) -> None:
    trainer = (await api.post("trainers", json=TRAINER)).json()["id"]
    other = (await api.post("trainers", json=TRAINER | {"name": "Other"})).json()["id"]
    data = CLASS | {"trainer_id": trainer}
    first = await api.post("classes", json=data)
    second = await api.post("classes", json=data | {"starts_at": "2030-04-30T23:45:00Z"})
    await api.post("classes", json=data | {"trainer_id": other})
    await api.post("classes", json=data | {"starts_at": "2030-05-01T00:00:00Z"})

    response = await api.get(
        "classes", params={"date": "2030-04-30", "trainer_id": trainer, "limit": 1, "offset": 1}
    )
    assert response.status_code == 200
    assert response.json() == [second.json()]
    path = f"classes/{first.json()['id']}"
    updated = await api.patch(path, json={"capacity": 4})
    assert updated.status_code == 200
    assert updated.json()["capacity"] == 4
    assert (await api.delete(path)).status_code == 204
    assert (await api.get(path)).status_code == 404
