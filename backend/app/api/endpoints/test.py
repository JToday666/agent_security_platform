from fastapi import APIRouter

api_test = APIRouter()

@api_test.get("/")
async def root():
    return {"message": "This is a test endpoint"}

@api_test.get('/get')
async def get_test():
    return {"message": "GET method response"}

# You can add more endpoints to this router as needed
# For example:
# @api_test.get("/another")
# async def another_test():
#     return {"message": "Another test endpoint"}
