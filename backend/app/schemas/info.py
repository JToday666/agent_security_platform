from pydantic import BaseModel


class InfoResponse(BaseModel):
    service: str
    environment: str
