from pydantic import BaseModel
from typing import Optional

class TariffPredictionRequest(BaseModel):
    """관세 예측 요청 DTO"""
    product_description: str
    price: Optional[float] = None
    quantity: Optional[int] = 1
    origin_country: Optional[str] = None
    shipping_cost: Optional[float] = 0
    scenario: Optional[str] = "해외직구"  # 해외직구, 해외체류 중 구매, 해외배송 