from httpx import AsyncClient

CLIENT = {
    "first_name": "Sam",
    "last_name": "Lee",
    "email": "sam@example.com",
    "phone": "+35712345678",
}


async def test_create_membership(api: AsyncClient) -> None:
    client = await api.post("clients", json=CLIENT)
    data = {
        "client_id": client.json()["id"],
        "start_date": "2030-05-01",
        "end_date": "2030-05-31",
    }
    response = await api.post("memberships", json=data)
    assert response.status_code == 201
    membership = response.json()
    assert membership == data | {"id": membership["id"], "status": "active"}
    assert (await api.get(f"memberships/{membership['id']}")).json() == membership
    assert (await api.get("memberships")).json() == [membership]
    assert (await api.post("memberships", json=data | {"client_id": 999})).status_code == 404


async def test_membership_date_validation_and_status_update(api: AsyncClient) -> None:
    client = await api.post("clients", json=CLIENT)
    data = {
        "client_id": client.json()["id"],
        "start_date": "2030-05-01",
        "end_date": "2030-05-31",
    }
    invalid = await api.post("memberships", json=data | {"end_date": "2030-04-30"})
    assert invalid.status_code == 422
    created = await api.post("memberships", json=data)
    path = f"memberships/{created.json()['id']}"
    invalid_patch = await api.patch(path, json={"start_date": "2030-06-01"})
    assert invalid_patch.status_code == 422
    assert (await api.get(path)).json() == created.json()
    updated = await api.patch(path, json={"status": "cancelled"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "cancelled"
