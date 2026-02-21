def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "v1"


def test_error_shape_for_unknown_route(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
