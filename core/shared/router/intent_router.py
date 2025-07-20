from langchain_core.messages import SystemMessage, AIMessage
import re
from typing import List, Optional

from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm
from core.shared.constants import (
    TARIFF_SESSION_KEYWORDS,
    NUMBER_SELECTION_PATTERNS,
    QUESTION_PATTERNS,
    INTENT_CLASSIFICATION_PROMPT,
    INTENT_TYPES,
    DEFAULT_INTENT,
    SESSION_CHECK_MESSAGE_COUNT
)


def _is_number_selection(query: str) -> bool:
    """숫자 선택 패턴인지 확인합니다."""
    return any(re.match(pattern, query) for pattern in NUMBER_SELECTION_PATTERNS)


def _is_question(query: str) -> bool:
    """질문 형태인지 확인합니다."""
    return any(re.search(pattern, query) for pattern in QUESTION_PATTERNS)


def _is_in_tariff_session(state: CustomsAgentState) -> bool:
    """관세 예측 세션 중인지 확인합니다."""
    # 1. state의 intent 필드 확인 (가장 중요)
    if state.get("intent") == "tariff_prediction":
        return True
    
    messages = state.get("messages", [])
    if not messages:
        return False
    
    # 2. 최근 메시지들을 확인하여 관세 예측 세션 중인지 판단
    recent_messages = messages[-SESSION_CHECK_MESSAGE_COUNT:]
    for msg in recent_messages:
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            content = msg.content.lower()
            if any(keyword in content for keyword in TARIFF_SESSION_KEYWORDS):
                return True
    
    # 3. 마지막 메시지에서 세션 상태 확인
    last_msg = messages[-1]
    if hasattr(last_msg, 'content') and isinstance(last_msg.content, str):
        content = last_msg.content.lower()
        if 'tariff_prediction' in content or '관세 예측 세션' in content:
            return True
    
    return False


def _classify_with_llm(query: str) -> str:
    """LLM을 사용하여 의도를 분류합니다."""
    try:
        llm = get_llm()
        result = llm.invoke([
            SystemMessage(content=INTENT_CLASSIFICATION_PROMPT.format(query=query))
        ])
        
        intent = str(result.content).strip()
        return intent if intent in INTENT_TYPES else DEFAULT_INTENT
        
    except Exception:
        # LLM 분류 실패 시 기본값 사용
        return DEFAULT_INTENT


def _add_classification_message(state: CustomsAgentState, intent: str, reason: str) -> None:
    """의도 분류 완료 메시지를 추가합니다."""
    state["messages"].append(
        AIMessage(content=f"의도 분류 완료: {intent} ({reason})")
    )


def intent_router(state: CustomsAgentState) -> CustomsAgentState:
    """사용자 쿼리의 의도를 분류합니다."""
    
    current_query = state["query"].strip()
    if not current_query:
        state["intent"] = DEFAULT_INTENT
        _add_classification_message(state, DEFAULT_INTENT, "빈 쿼리")
        return state
    
    # 세션 연속성 확인
    is_in_tariff_session = _is_in_tariff_session(state)
    
    # 관세 예측 세션 중이면 무조건 tariff_prediction으로 분류
    if is_in_tariff_session:
        state["intent"] = "tariff_prediction"
        _add_classification_message(state, "tariff_prediction", "관세 예측 세션 연속성 유지")
        return state
    
    # 패턴 기반 분류
    is_number_selection = _is_number_selection(current_query)
    is_question = _is_question(current_query)
    
    # 질문 형태이면서 관세 예측 세션이 아닌 경우 QnA로 분류
    if is_question:
        state["intent"] = "qna"
        _add_classification_message(state, "qna", "질문 형태 감지")
        return state
    
    # 숫자 선택이지만 관세 예측 세션이 아닌 경우에도 tariff_prediction으로 분류
    # (HS 코드 직접 입력 등의 경우)
    if is_number_selection:
        state["intent"] = "tariff_prediction"
        _add_classification_message(state, "tariff_prediction", "숫자 선택 감지")
        return state
    
    # LLM 기반 의도 분류를 수행
    intent = _classify_with_llm(current_query)
    state["intent"] = intent
    _add_classification_message(state, intent, "LLM 분류")
    
    return state