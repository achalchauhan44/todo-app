from fastapi import FastAPI
from database import get_task_collection
from routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ToDo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
