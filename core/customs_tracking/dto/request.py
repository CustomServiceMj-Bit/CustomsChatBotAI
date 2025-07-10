from pydantic import BaseModel

class TrackDeliveryRequest(BaseModel):
    message: str
