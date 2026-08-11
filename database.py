from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
if DB_NAME is None:
	raise RuntimeError("DB_NAME is not set")

db = client[DB_NAME]

def get_task_collection():
    return db["tasks"]

def get_user_collection():
    return db["users"]