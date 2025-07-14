from pydantic import BaseModel
from typing import List, Optional

class HSClassificationResult(BaseModel):
    """HS 코드 분류 결과"""
    hs_code: str
    probability: str
    description: Optional[str] = None

class TariffCalculationResult(BaseModel):
    """관세 계산 결과"""
    hs_code: str
    tariff_rate: float
    tariff_amount: float
    vat_amount: float
    total_tax: float
    fta_applied: bool
    applied_rule: str
    notes: Optional[str] = None

class ExchangeRateResult(BaseModel):
    """환율 정보"""
    currency: str
    rate: float
    date: str

class TariffPredictionResponse(BaseModel):
    """관세 예측 응답 DTO"""
    product_description: str
    hs_classifications: List[HSClassificationResult]
    tariff_calculation: Optional[TariffCalculationResult] = None
    exchange_rate: Optional[ExchangeRateResult] = None
    total_response: str 