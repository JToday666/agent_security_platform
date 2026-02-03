from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "my first fastapi project"}

@app.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"hello {name}"}

@app.get("/id/{m_id}")
async def my(m_id:int):
    return {"message": f"your id is {m_id}"}

@app.get("/my/{name},{age}/{addr}")
async def test_one(name: str, age: int, addr: str):
    return {"name": name, "age": age, "addr": addr}
