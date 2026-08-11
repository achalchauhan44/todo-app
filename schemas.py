from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TaskCreate(BaseModel):
    title: str
    completed: bool = False

class TaskUpdate(BaseModel):
    title: str
    completed: bool

class TaskPatch(BaseModel):
    title: str | None = None
    completed: bool | None = None
class TaskResponse(BaseModel):
    id: str
    title: str
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class SortField(str, Enum):
    created_at = "created_at"
    updated_at = "updated_at"
    task_title = "title" 

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"