import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient
from main import app

TEST_MONGO_URI = "mongodb+srv://achalchauhan44:achal7272@todocluster.qm7ijm9.mongodb.net/?appName=ToDoCluster"  # or your Atlas URI
TEST_DB_NAME = "todo_test_db"

@pytest_asyncio.fixture
async def test_db():
    client = AsyncIOMotorClient(TEST_MONGO_URI)
    db = client[TEST_DB_NAME]
    yield db
    # Cleanup: wipe the test database after each test
    await client.drop_database(TEST_DB_NAME)
    client.close()

@pytest.fixture
def client():
    return TestClient(app)

# tests/conftest.py — add this
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app

@pytest_asyncio.fixture
async def authed_client(test_db, monkeypatch):
    # Point the app's real dependency at the test database
    from database import get_task_collection, get_user_collection

    async def override_get_task_collection():
        return test_db["tasks"]

    async def override_get_user_collection():
        return test_db["users"]

    app.dependency_overrides[get_task_collection] = override_get_task_collection
    app.dependency_overrides[get_user_collection] = override_get_user_collection

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/signup", json={"email": "test@example.com", "password": "testpass123"})
        login_response = await ac.post("/login", json={"email": "test@example.com", "password": "testpass123"})
        token = login_response.json()["access_token"]
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac

    app.dependency_overrides.clear()