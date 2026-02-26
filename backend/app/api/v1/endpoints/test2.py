from fastapi import APIRouter

router = APIRouter(prefix="/test2", tags=["test2"])

@router.get("/hello")
async def hello():
    return {"message": "Hello from test2!"}
