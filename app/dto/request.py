from pydantic import BaseModel

class Request(BaseModel):
    message: str
    session_id: str = None
