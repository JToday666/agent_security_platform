from fastapi import FastAPI
from api.router import api_router

app = FastAPI(title="FastAPI 项目")

app.include_router(api_router, prefix="/api", tags=["api"])

@app.get("/")
async def read_root():
    return {"message": "Hello my first FastAPI project!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8001, reload=True)
    