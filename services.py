from bson import ObjectId
from datetime import datetime, timezone
from typing import Any

# NOTE: no more "from database import task_collection" — passed in per-call instead

def ensure_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def task_helper(task) -> dict:
    return {
        "id": str(task["_id"]),
        "title": task["title"],
        "completed": task["completed"],
        "created_at": ensure_utc(task["created_at"]),
        "updated_at": ensure_utc(task.get("updated_at")),
        "completed_at": ensure_utc(task.get("completed_at")),
    }

async def create_task(task_collection, task_data: dict, user_id: str) -> dict:
    task_data["user_id"] = user_id
    task_data["created_at"] = datetime.now(timezone.utc)
    task_data["updated_at"] = None
    task_data["completed_at"] = None
    result = await task_collection.insert_one(task_data)
    new_task = await task_collection.find_one({"_id": result.inserted_id})
    return task_helper(new_task)

async def get_all_tasks(
    task_collection,
    user_id: str,
    completed: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    order: str = "desc",
) -> list:
    query: dict[str, Any] = {"user_id": user_id}
    if completed is not None:
        query["completed"] = completed

    direction = -1 if order == "desc" else 1

    tasks = []
    cursor = (
        task_collection.find(query)
        .sort(sort_by, direction)
        .skip(skip)
        .limit(limit)
    )
    async for task in cursor:
        tasks.append(task_helper(task))
    return tasks

async def get_task_by_id(task_collection, task_id: str, user_id: str):
    task = await task_collection.find_one({"_id": ObjectId(task_id), "user_id": user_id})
    if task:
        return task_helper(task)
    return None

async def update_task(task_collection, task_id: str, task_data: dict, user_id: str):
    existing = await task_collection.find_one({"_id": ObjectId(task_id), "user_id": user_id})
    if existing is None:
        return None

    now = datetime.now(timezone.utc)
    update_fields = dict(task_data)

    if task_data.get("title") != existing.get("title"):
        update_fields["updated_at"] = now

    update_fields["completed_at"] = now if task_data.get("completed") else None

    await task_collection.update_one(
        {"_id": ObjectId(task_id), "user_id": user_id}, {"$set": update_fields}
    )
    updated_task = await task_collection.find_one({"_id": ObjectId(task_id)})
    return task_helper(updated_task)

async def delete_task(task_collection, task_id: str, user_id: str) -> bool:
    result = await task_collection.delete_one({"_id": ObjectId(task_id), "user_id": user_id})
    return result.deleted_count > 0

async def patch_task(task_collection, task_id: str, update_fields: dict, user_id: str):
    if not update_fields:
        raise ValueError("No fields provided to update")

    existing = await task_collection.find_one({"_id": ObjectId(task_id), "user_id": user_id})
    if existing is None:
        return None

    now = datetime.now(timezone.utc)

    if "title" in update_fields and update_fields["title"] != existing.get("title"):
        update_fields["updated_at"] = now

    if "completed" in update_fields:
        update_fields["completed_at"] = now if update_fields["completed"] else None

    await task_collection.update_one(
        {"_id": ObjectId(task_id), "user_id": user_id}, {"$set": update_fields}
    )
    updated_task = await task_collection.find_one({"_id": ObjectId(task_id)})
    return task_helper(updated_task)