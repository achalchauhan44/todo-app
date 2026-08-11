import pytest
from services import create_task, get_task_by_id

pytestmark = pytest.mark.asyncio

async def test_create_task_stores_correct_fields(test_db):
    task_collection = test_db["tasks"]

    task_data = {"title": "Buy groceries", "completed": False}
    result = await create_task(task_collection, task_data, user_id="fake_user_123")

    assert result["title"] == "Buy groceries"
    assert result["completed"] is False
    assert result["created_at"] is not None
    assert "id" in result

async def test_get_task_by_id_returns_none_for_wrong_user(test_db):
    task_collection = test_db["tasks"]

    task_data = {"title": "Private task", "completed": False}
    created = await create_task(task_collection, task_data, user_id="user_a")

    # Try fetching it as a different user
    result = await get_task_by_id(task_collection, created["id"], user_id="user_b")

    assert result is None