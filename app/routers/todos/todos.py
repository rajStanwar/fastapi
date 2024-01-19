from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Path

from app.utils.static_values import MONGO_ID_REGEX
from app.utils.db import db

from .models import NotFoundException, Todo, TodoId, TodoRecord

router = APIRouter()

@router.post("/todo", response_model=TodoId)
async def create_todo(payload: Todo) -> TodoId:
    """Create a new todo
    Args:
        payload (Todo): title and completed status

    Returns:
        TodoId: the id of the created todo
    """
    now = datetime.utcnow()
    insert_result = await db.todos.insert_one(
        {
            "title": payload.title,
            "completed": payload.completed,
            "created_date": now,
            "updated_date": now,
        }
    )
    return TodoId(id=str(insert_result.inserted_id))

@router.get("/todos", response_model=list[TodoRecord])
async def get_todos() -> list[TodoRecord]:
    """Get all todos
    Returns:
        list[TodoRecord]: list of todos
    """
    todos: list[TodoRecord] = []
    async for doc in db.todos.find():
        todos.append(
            TodoRecord(
                id=str(doc['_id']),
                title=doc['title'],
                completed=doc['completed'],
                created_date=doc['created_date'],
                updated_date=doc['updated_date'],
            )
        )
    return todos


@router.get("/todo/{id}", response_model=TodoRecord)
async def get_todo(id: str = Path(description="Todo ID", pattern=MONGO_ID_REGEX)) -> TodoRecord:
    """
    Get a todo item by ID
    """
    doc = await db.todos.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Not Found")
    return TodoRecord(
        id=str(doc["_id"]),
        title=doc["title"],
        completed=doc["completed"],
        created_date=doc["created_date"],
        updated_date=doc["updated_date"],
    )
    
@router.put("/todo/{id}", response_model=TodoId, responses={404: {"description": "Not Found", "model": NotFoundException}})
async def update_todo(payload: Todo, id: str = Path(description="Todo ID", pattern=MONGO_ID_REGEX)) -> TodoId:
    """
    Update a todo
    """
    now = datetime.utcnow()
    update_result = await db.todos.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"title": payload.title, "completed": payload.completed, "updated_date": now}},
    )
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not Found")
    return TodoId(id=id)   

@router.delete("/todo/{id}", response_model=bool, responses={404: {"description": "Not Found", "model": NotFoundException}}) 
async def delete_todo(id: str = Path(description="Todo ID", pattern=MONGO_ID_REGEX)) -> bool:
    """
    Delete a todo item by ID
    """
    delete_result = await db.todos.delete_one({"_id": ObjectId(id)})
    
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not Found")
    
    return True