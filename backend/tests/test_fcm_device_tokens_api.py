async def test_fcm_device_token_can_be_saved_and_deleted(client, auth_headers):
    token = "fcm-device-token-that-is-long-enough-for-validation"

    response = await client.post(
        "/api/v1/fcm-device-tokens",
        headers=auth_headers,
        json={"token": token, "platform": "android"},
    )
    assert response.status_code == 204

    response = await client.request(
        "DELETE",
        "/api/v1/fcm-device-tokens",
        headers=auth_headers,
        json={"token": token},
    )
    assert response.status_code == 204
