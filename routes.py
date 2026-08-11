from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson.errors import InvalidId
from schemas import TaskCreate, TaskUpdate, TaskResponse, UserCreate, UserLogin, Token, TaskPatch, SortField, SortOrder
from database import get_task_collection, get_user_collection
from auth import hash_password, verify_password, create_access_token, get_current_user
from services import (
    create_task,
    get_all_tasks,
    get_task_by_id,
    update_task,
    delete_task,
    patch_task,
)

router = APIRouter()


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    current_user: dict = Depends(get_current_user),
    task_collection=Depends(get_task_collection),
    completed: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    sort_by: SortField = SortField.created_at,
    order: SortOrder = SortOrder.desc,
):
    return await get_all_tasks(
        task_collection,
        user_id=current_user["id"],
        completed=completed,
        skip=skip,
        limit=limit,
        sort_by=sort_by.value,
        order=order.value,
    )


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def add_task(
    task: TaskCreate,
    current_user: dict = Depends(get_current_user),
    task_collection=Depends(get_task_collection),
):
    task_data = task.model_dump()
    return await create_task(task_collection, task_data, user_id=current_user["id"])


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def read_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    task_collection=Depends(get_task_collection),
):
    try:
        task = await get_task_by_id(task_collection, task_id, user_id=current_user["id"])
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task ID format")
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def edit_task(
    task_id: str,
    task: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    task_collection=Depends(get_task_collection),
):
    try:
        updated = await update_task(task_collection, task_id, task.model_dump(), user_id=current_user["id"])
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task ID format")
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    task_collection=Depends(get_task_collection),
):
    try:
        deleted = await delete_task(task_collection, task_id, user_id=current_user["id"])
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task ID format")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return None


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def patch_task_route(
    task_id: str,
    task: TaskPatch,
    current_user: dict = Depends(get_current_user),
    task_collection=Depends(get_task_collection),
):
    update_fields = task.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided",
        )
    try:
        updated = await patch_task(task_collection, task_id, update_fields, user_id=current_user["id"])
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task ID format")
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, user_collection=Depends(get_user_collection)):
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed_pw = hash_password(user.password)
    new_user = {
        "email": user.email,
        "hashed_password": hashed_pw,
    }
    result = await user_collection.insert_one(new_user)
    return {"id": str(result.inserted_id), "email": user.email}


@router.post("/login", response_model=Token)
async def login(user: UserLogin, user_collection=Depends(get_user_collection)):
    db_user = await user_collection.find_one({"email": user.email})
    invalid_credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if db_user is None:
        raise invalid_credentials_exception
    if not verify_password(user.password, db_user["hashed_password"]):
        raise invalid_credentials_exception
    access_token = create_access_token(data={"sub": str(db_user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}