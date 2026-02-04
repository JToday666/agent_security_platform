from fastapi import FastAPI

app = FastAPI(title="VS Code FastAPI 项目")

@app.get("/")
async def read_root():
    return {"message": "Hello from VS Code!"}
