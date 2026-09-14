async def test_web_push_configuration_is_disabled_without_vapid_keys(client, auth_headers):
    response = await client.get(
        "/api/v1/push-subscriptions/configuration", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json() == {"enabled": False, "public_key": None}


async def test_push_subscription_can_be_saved_and_deleted(client, auth_headers):
    subscription = {
        "endpoint": "https://push.example.test/subscriptions/guardian-1",
        "keys": {"p256dh": "public-encryption-key", "auth": "authentication-secret"},
    }

    created = await client.post(
        "/api/v1/push-subscriptions", headers=auth_headers, json=subscription
    )
    deleted = await client.request(
        "DELETE",
        "/api/v1/push-subscriptions",
        headers=auth_headers,
        json={"endpoint": subscription["endpoint"]},
    )

    assert created.status_code == 204
    assert deleted.status_code == 204
