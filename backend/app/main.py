from fastapi import FastAPI
from .core.config import settings
from .api.router import api_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router)

@app.get("/")
async def read_root():
    return {"message": "Hello FastAPI project!" + " settings.PROJECT_NAME: " + settings.PROJECT_NAME}
