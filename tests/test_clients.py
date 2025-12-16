from httpx import AsyncClient

CLIENT = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "phone": "+35712345678",
}


async def test_create_client(api: AsyncClient) -> None:
    response = await api.post("clients", json=CLIENT)
    assert response.status_code == 201
    assert response.json() | CLIENT == response.json()
    assert response.json()["id"] > 0
    assert response.json()["created_at"]


async def test_duplicate_email_in_create_and_patch(api: AsyncClient) -> None:
    first = await api.post("clients", json=CLIENT)
    assert first.status_code == 201
    duplicate = await api.post("clients", json=CLIENT | {"email": "ADA@EXAMPLE.COM"})
    assert duplicate.status_code == 409

    second = await api.post("clients", json=CLIENT | {"email": "grace@example.com"})
    client_id = second.json()["id"]
    response = await api.patch(f"clients/{client_id}", json={"email": CLIENT["email"]})
    assert response.status_code == 409
    assert (await api.get(f"clients/{client_id}")).json()["email"] == "grace@example.com"


async def test_get_client(api: AsyncClient) -> None:
    created = await api.post("clients", json=CLIENT)
    response = await api.get(f"clients/{created.json()['id']}")
    assert response.status_code == 200
    assert response.json() == created.json()
    assert (await api.get("clients/999")).status_code == 404


async def test_client_pagination_update_and_delete(api: AsyncClient) -> None:
    await api.post("clients", json=CLIENT)
    second = await api.post("clients", json=CLIENT | {"email": "second@example.com"})
    assert (await api.get("clients", params={"limit": 1, "offset": 1})).json() == [second.json()]
    path = f"clients/{second.json()['id']}"
    updated = await api.patch(path, json={"first_name": "Grace"})
    assert updated.status_code == 200
    assert updated.json()["first_name"] == "Grace"
    deleted = await api.delete(path)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert (await api.get(path)).status_code == 404


async def test_client_input_validation(api: AsyncClient) -> None:
    assert (await api.post("clients", json=CLIENT | {"email": "invalid"})).status_code == 422
    assert (await api.patch("clients/1", json={"phone": None})).status_code == 422
    assert (await api.get("clients", params={"limit": 101})).status_code == 422
