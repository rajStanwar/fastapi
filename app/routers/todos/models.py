from pydantic import BaseModel
from datetime import datetime


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