from httpx import AsyncClient


async def test_signup_login_and_current_user(client: AsyncClient) -> None:
    credentials = {"email": "auth@example.com", "password": "password1234"}

    signup_response = await client.post("/api/v1/auth/signup", json=credentials)
    assert signup_response.status_code == 201
    signup_body = signup_response.json()
    assert signup_body["token_type"] == "bearer"
    assert signup_body["user"]["email"] == credentials["email"]
    assert "password" not in signup_body["user"]

    duplicate_response = await client.post("/api/v1/auth/signup", json=credentials)
    assert duplicate_response.status_code == 409

    login_response = await client.post("/api/v1/auth/login", json=credentials)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == credentials["email"]


async def test_login_rejects_invalid_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "auth@example.com", "password": "password1234"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "auth@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_update_current_user(client: AsyncClient) -> None:
    credentials = {"email": "before@example.com", "password": "password1234"}
    signup_response = await client.post("/api/v1/auth/signup", json=credentials)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_response = await client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={
            "current_password": credentials["password"],
            "email": "after@example.com",
            "new_password": "new-password1234",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["email"] == "after@example.com"

    old_login = await client.post("/api/v1/auth/login", json=credentials)
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "after@example.com", "password": "new-password1234"},
    )
    assert new_login.status_code == 200


async def test_update_current_user_rejects_wrong_password(client: AsyncClient) -> None:
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "auth@example.com", "password": "password1234"},
    )
    token = signup_response.json()["access_token"]

    response = await client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "wrong-password", "email": "new@example.com"},
    )
    assert response.status_code == 401


async def test_protected_api_requires_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/people")
    assert response.status_code == 401
