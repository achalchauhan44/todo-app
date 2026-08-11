import pytest

pytestmark = pytest.mark.asyncio

async def test_create_and_list_task(authed_client):
    create_response = await authed_client.post("/tasks", json={"title": "Write tests", "completed": False})
    assert create_response.status_code == 201
    assert create_response.json()["title"] == "Write tests"

    list_response = await authed_client.get("/tasks")
    assert list_response.status_code == 200
    tasks = list_response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Write tests"

async def test_create_task_without_token_returns_401(test_db):
    from httpx import ASGITransport, AsyncClient
    from main import app
    from database import get_task_collection

    async def override_get_task_collection():
        return test_db["tasks"]

    app.dependency_overrides[get_task_collection] = override_get_task_collection

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/tasks", json={"title": "No auth", "completed": False})

    assert response.status_code == 401
    app.dependency_overrides.clear()

# tests/test_routes.py — add this
async def test_user_cannot_access_another_users_task(test_db):
    from httpx import ASGITransport, AsyncClient
    from main import app
    from database import get_task_collection, get_user_collection

    async def override_tasks():
        return test_db["tasks"]

    async def override_users():
        return test_db["users"]

    app.dependency_overrides[get_task_collection] = override_tasks
    app.dependency_overrides[get_user_collection] = override_users

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User A signs up, logs in, creates a task
        await ac.post("/signup", json={"email": "usera@example.com", "password": "passwordA"})
        login_a = await ac.post("/login", json={"email": "usera@example.com", "password": "passwordA"})
        token_a = login_a.json()["access_token"]

        create_response = await ac.post(
            "/tasks",
            json={"title": "User A's private task", "completed": False},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        task_id = create_response.json()["id"]

        # User B signs up, logs in
        await ac.post("/signup", json={"email": "userb@example.com", "password": "passwordB"})
        login_b = await ac.post("/login", json={"email": "userb@example.com", "password": "passwordB"})
        token_b = login_b.json()["access_token"]

        # User B tries to access User A's task
        get_response = await ac.get(
            f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token_b}"}
        )
        delete_response = await ac.delete(
            f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token_b}"}
        )

    assert get_response.status_code == 404
    assert delete_response.status_code == 404

    app.dependency_overrides.clear()

async def test_login_with_wrong_password_returns_401(test_db):
    from httpx import ASGITransport, AsyncClient
    from main import app
    from database import get_user_collection

    async def override_users():
        return test_db["users"]

    app.dependency_overrides[get_user_collection] = override_users

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/signup", json={"email": "user@example.com", "password": "correctpass"})
        response = await ac.post("/login", json={"email": "user@example.com", "password": "wrongpass"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

    app.dependency_overrides.clear()

async def test_login_with_nonexistent_email_returns_401(test_db):
    from httpx import ASGITransport, AsyncClient
    from main import app
    from database import get_user_collection

    async def override_users():
        return test_db["users"]

    app.dependency_overrides[get_user_collection] = override_users

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/login", json={"email": "ghost@example.com", "password": "anything"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

    app.dependency_overrides.clear()

async def test_expired_token_returns_401(test_db):
    from httpx import ASGITransport, AsyncClient
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from main import app
    from config import SECRET_KEY, ALGORITHM
    from database import get_task_collection, get_user_collection

    async def override_tasks():
        return test_db["tasks"]

    async def override_users():
        return test_db["users"]

    app.dependency_overrides[get_task_collection] = override_tasks
    app.dependency_overrides[get_user_collection] = override_users

    # Manually craft a token that expired 5 minutes ago
    expired_payload = {
        "sub": "000000000000000000000000",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/tasks", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401

    app.dependency_overrides.clear()
