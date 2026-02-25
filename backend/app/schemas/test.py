from pydantic import BaseModel, Field ,EmailStr

class Test(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    email: EmailStr