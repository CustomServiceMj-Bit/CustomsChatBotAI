from langchain_core.messages import SystemMessage, AIMessage

from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm

def intent_router(state: CustomsAgentState) -> CustomsAgentState:
    """사용자 쿼리의 의도를 분류합니다."""
    llm = get_llm()
    
    classification_prompt = """
    다음 사용자 쿼리를 분석하여 정확히 하나의 카테고리로 분류해주세요:

    1. customs_tracking: 통관 조회, 운송장 추적, 배송 상태 관련
    2. tariff_prediction: 관세 계산, 세율 문의, 관세 예측 관련  
    3. qna: 일반적인 관세/통관 관련 질문, 법령 문의, 절차 안내

    사용자 쿼리: {query}

    반드시 다음 중 하나만 응답하세요: customs_tracking, tariff_prediction, qna
    """
    
    result = llm.invoke([
        SystemMessage(content=classification_prompt.format(query=state["query"]))
    ])
    
    intent = result.content.strip()
    if intent not in ["customs_tracking", "tariff_prediction", "qna"]:
        intent = "qna"  # 기본값
    
    state["intent"] = intent
    state["messages"].append(AIMessage(content=f"의도 분류 완료: {intent}"))
    print(state)
    return state