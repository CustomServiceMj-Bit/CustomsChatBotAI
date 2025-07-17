from pydantic import BaseModel
from typing import Optional, Literal

class TariffPredictionRequest(BaseModel):
    step: Literal["input", "hs6_select", "hs10_select"]  # 현재 단계
    product_description: Optional[str] = None  # 상품 설명 (input 단계)
    hs6_code: Optional[str] = None             # 선택한 HS6 코드 (hs6_select 단계)
    hs10_code: Optional[str] = None            # 선택한 HS10 코드 (hs10_select 단계)
    origin_country: Optional[str] = None       # 원산지 국가 (hs10_select 단계)
    price: Optional[float] = None              # 상품 가격 (hs10_select 단계)
    quantity: Optional[int] = 1                # 수량 (hs10_select 단계)
    shipping_cost: Optional[float] = 0         # 배송비 (hs10_select 단계)
    scenario: Optional[str] = "해외직구"         # 시나리오 (hs10_select 단계) 