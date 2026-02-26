from fastapi import APIRouter

router = APIRouter(prefix="/test1", tags=["test1"])

@router.get("/hello")
async def hello():
    return {"message": "Hello from test1!"}
