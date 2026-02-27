from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(title=settings.PROJECT_NAME)

Path("uploads").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and {"code", "message", "data"}.issubset(exc.detail.keys()):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": str(exc.detail),
            "data": None,
        },
    )

app.include_router(api_router)

@app.get("/")
async def read_root():
    return {"message": "Hello FastAPI project!" + " PROJECT_NAME: " + settings.PROJECT_NAME}
