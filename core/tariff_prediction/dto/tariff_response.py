from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal

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
    step: Literal["hs6_select", "hs10_select", "result"]  # 다음 단계
    hs6_candidates: Optional[List[Dict[str, Any]]] = None     # HS6 후보 리스트 (input 단계 응답)
    hs10_candidates: Optional[List[Dict[str, Any]]] = None    # HS10 후보 리스트 (hs6_select 단계 응답)
    calculation_result: Optional[Dict[str, Any]] = None       # 관세 계산 결과 (hs10_select 단계 응답)
    message: Optional[str] = None                             # 안내/에러 메시지 