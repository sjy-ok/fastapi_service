async def test_health_and_request_id(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]

    response = await client.get("/health", headers={"X-Request-ID": "known-id"})
    assert response.headers["X-Request-ID"] == "known-id"


async def test_frontend_is_served(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "人员管理台" in response.text

    response = await client.get("/static/app.js")
    assert response.status_code == 200
    assert "Personnel" not in response.text[:20]
