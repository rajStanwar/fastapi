import time
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Callable, TypeVar
from app.utils.config import settings
from app.utils.logger import logger
from app.routers.todos.todos import router as todos_router

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


app.include_router(
    todos_router,
    prefix="/v1/todos",
    tags=["todos"],
)

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}

 
if __name__== "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="debug", reload=True)