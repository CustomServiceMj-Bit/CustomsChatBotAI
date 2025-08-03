from pydantic import BaseModel

class Request(BaseModel):
    message: str
