# 상태 정의
from typing import List, Optional, Literal, Dict, Any
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage


class CustomsAgentState(TypedDict):
    """관세청 에이전트 상태"""
    messages: List[BaseMessage]
    query: str
    intent: Optional[Literal["customs_tracking", "tariff_prediction", "qna"]]
    final_response: str
    intermediate_results: Dict[str, Any]