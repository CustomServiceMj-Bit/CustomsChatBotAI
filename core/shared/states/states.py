# 상태 정의
from typing import List, Optional, Literal, Dict, Any

from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage

from core.customs_tracking.dto.progress_detail import ProgressDetail

class CustomsAgentState(TypedDict):
    """관세청 에이전트 상태"""
    messages: List[BaseMessage]
    query: str
    intent: Optional[Literal["customs_tracking", "tariff_prediction", "qna"]]
    final_response: str
    intermediate_results: Dict[str, Any]
    progress_details: Optional[List[ProgressDetail]]
    error_reason: Optional[str]