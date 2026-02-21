def test_rate_limit_triggers(client):
    headers = {"x-dev-user-id": "rate-limit-user"}
    assert client.get("/api/v1/health", headers=headers).status_code == 200
    assert client.get("/api/v1/health", headers=headers).status_code == 200

    third = client.get("/api/v1/health", headers=headers)
    assert third.status_code == 429
    payload = third.json()
    assert payload["error"]["code"] == "RATE_LIMITED"
