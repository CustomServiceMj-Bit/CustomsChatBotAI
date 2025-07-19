from langchain_core.messages import SystemMessage, AIMessage
import re

from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm
from core.shared.constants import (
    TARIFF_SESSION_KEYWORDS,
    NUMBER_SELECTION_PATTERNS,
    TARIFF_PREDICTION_KEYWORDS,
    CUSTOMS_TRACKING_KEYWORDS,
    INTENT_CLASSIFICATION_PROMPT,
    INTENT_TYPES,
    DEFAULT_INTENT
)

def intent_router(state: CustomsAgentState) -> CustomsAgentState:
    """사용자 쿼리의 의도를 분류합니다."""
    
    # 이전 대화에서 관세 예측 중인지 확인
    messages = state.get("messages", [])
    is_in_tariff_session = False
    
    # 최근 메시지들을 확인하여 관세 예측 세션 중인지 판단
    for msg in messages[-5:]:  # 최근 5개 메시지 확인
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            content = msg.content.lower()
            # 관세 예측 관련 키워드가 있거나 HS 코드 선택 메시지가 있으면 관세 예측 세션으로 판단
            if any(keyword in content for keyword in TARIFF_SESSION_KEYWORDS):
                is_in_tariff_session = True
                break
    
    # 이전 의도가 tariff_prediction이었는지도 확인
    if messages and len(messages) > 0:
        last_msg = messages[-1]
        if hasattr(last_msg, 'content') and isinstance(last_msg.content, str):
            if 'tariff_prediction' in last_msg.content:
                is_in_tariff_session = True
    
    # 관세 예측 세션 중이면 무조건 tariff_prediction으로 분류
    if is_in_tariff_session:
        state["intent"] = "tariff_prediction"  # type: ignore
        state["messages"].append(AIMessage(content=f"의도 분류 완료: {state['intent']} (관세 예측 세션 연속성 유지)"))
        print(state)
        return state
    
    # 현재 쿼리가 숫자 선택인지 확인
    current_query = state["query"].strip()
    is_number_selection = False
    
    # 숫자 선택 패턴 확인 (1번, 2번, 3번, 1, 2, 3 등)
    for pattern in NUMBER_SELECTION_PATTERNS:
        if re.match(pattern, current_query):
            is_number_selection = True
            break
    
    # 관세 예측 세션 중이고 숫자 선택이면 무조건 tariff_prediction
    if is_in_tariff_session and is_number_selection:
        state["intent"] = "tariff_prediction"  # type: ignore
        state["messages"].append(AIMessage(content=f"의도 분류 완료: {state['intent']} (세션 연속성 유지)"))
        print(state)
        return state
    
    # 숫자 선택이지만 관세 예측 세션이 아닌 경우에도 tariff_prediction으로 분류
    # (HS 코드 직접 입력 등의 경우)
    if is_number_selection:
        state["intent"] = "tariff_prediction"  # type: ignore
        state["messages"].append(AIMessage(content=f"의도 분류 완료: {state['intent']} (숫자 선택 감지)"))
        print(state)
        return state
    
    # 관세 예측 관련 키워드가 있으면 무조건 tariff_prediction으로 분류
    current_query_lower = current_query.lower()
    if any(keyword in current_query_lower for keyword in TARIFF_PREDICTION_KEYWORDS):
        state["intent"] = "tariff_prediction"  # type: ignore
        state["messages"].append(AIMessage(content=f"의도 분류 완료: {state['intent']} (관세 예측 키워드 감지)"))
        print(state)
        return state
    
    # 운송장/배송 관련 키워드가 있으면 customs_tracking으로 분류
    if any(keyword in current_query_lower for keyword in CUSTOMS_TRACKING_KEYWORDS):
        state["intent"] = "customs_tracking"  # type: ignore
        state["messages"].append(AIMessage(content=f"의도 분류 완료: {state['intent']} (배송 추적 키워드 감지)"))
        print(state)
        return state
    
    # 일반적인 의도 분류 (LLM 사용)
    llm = get_llm()
    
    try:
        result = llm.invoke([
            SystemMessage(content=INTENT_CLASSIFICATION_PROMPT.format(query=state["query"]))
        ])
        
        intent = str(result.content).strip()
        if intent not in INTENT_TYPES:
            intent = DEFAULT_INTENT  # 기본값을 tariff_prediction으로 변경
    except Exception as e:
        print(f"[DEBUG] LLM 분류 오류: {e}")
        intent = DEFAULT_INTENT  # 오류 시에도 tariff_prediction으로 분류
    
    state["intent"] = intent  # type: ignore
    state["messages"].append(AIMessage(content=f"의도 분류 완료: {intent}"))
    print(state)
    return state