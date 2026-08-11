def test_signup_missing_body_returns_422(client):
    response = client.post("/signup")
    assert response.status_code == 422