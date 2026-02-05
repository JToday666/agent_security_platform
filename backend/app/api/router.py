from fastapi import APIRouter
from .endpoints.test import api_test

api_router = APIRouter()
api_router.include_router(api_test, prefix="/test", tags=["test"])

# You can include more routers here as your application grows

# For example:
# from endpoints.user import api_user
# api_router.include_router(api_user, prefix="/user", tags=["user"])

# Now, api_router can be included in the main FastAPI app
