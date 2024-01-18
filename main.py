from bson import ObjectId
import uvicorn
from fastapi import FastAPI, HTTPException, Path, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
import logging
import sys
import time
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Callable, TypeVar

load_dotenv()

MONGO_ID_REGEX = r"^[a-f\d]{24}$"

class Settings(BaseSettings):
    mongo_uri: str
    root_path: str = ""
    logging_level: str = "INFO"
    model_config: SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

logging.basicConfig(
    stream=sys.stdout,
    level=settings.logging_level,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",
)

logger = logging.getLogger("my-todos")

db_client = AsyncIOMotorClient(settings.mongo_uri)
db = db_client.todoDb

description = """
This is a fancy API built with [FastAPI🚀](https://fastapi.tiangolo.com/)

📝 [Source Code](https://github.com/rajStanwar/fastapi_auth)  
🐞 [Issues](https://github.com/rajStanwar/fastapi_auth/issues) 
"""

app = FastAPI(
    title="My Todo App",
    description=description,
    version="1.0.0",
    docs_url="/",
    root_path=settings.root_path
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"],
)

F = TypeVar("F", bound=Callable[..., Any])

@app.middleware("http")
async def process_time_log_middleware(request: Request, call_next: F) -> Response:
    """
    Add API process time in response headers and log calls
    """
    start_time = time.time()
    response: Response = await call_next(request)
    proces_time = str(round(time.time() - start_time, 3))
    response.headers['X-Process-Time'] = proces_time
    
    logger.info(
        "Method=%s Path=%s StatusCode=%s ProcessTime=%s",
        request.method,
        request.url.path,
        response.status_code,
        proces_time
    )
    
    return response
class Todo(BaseModel):
    title: str
    completed: bool = False
    

class TodoId(BaseModel):
    id: str


class TodoRecord(TodoId, Todo):
    created_date: datetime
    updated_date: datetime


class NotFoundException(BaseModel):
    detail: str = "Not Found"  


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.get("/item/{item_id}")
async def read_item(item_id: str) -> dict[str, int]:
    return {"item_id": item_id}


@app.post("/todo", response_model=TodoId)
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

@app.get("/todos", response_model=list[TodoRecord])
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


@app.get("/todo/{id}", response_model=TodoRecord)
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
    
@app.put("/todo/{id}", response_model=TodoId, responses={404: {"description": "Not Found", "model": NotFoundException}})
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

@app.delete("/todo/{id}", response_model=bool, responses={404: {"description": "Not Found", "model": NotFoundException}}) 
async def delete_todo(id: str = Path(description="Todo ID", pattern=MONGO_ID_REGEX)) -> bool:
    """
    Delete a todo item by ID
    """
    delete_result = await db.todos.delete_one({"_id": ObjectId(id)})
    
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not Found")
    
    return True
    
    
    
if __name__== "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="debug", reload=True)