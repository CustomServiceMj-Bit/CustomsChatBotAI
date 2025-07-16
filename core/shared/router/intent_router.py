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

    # 예시
    - "관세 예측해줘" → tariff_prediction
    - "관세 계산해줘" → tariff_prediction
    - "관세 알려줘" → tariff_prediction
    - "이 물건의 세금이 얼마나 나올까?" → tariff_prediction
    - "운송장 번호 123456 어디쯤이야?" → customs_tracking
    - "통관 진행 상황 알려줘" → customs_tracking
    - "관세청 전화번호 알려줘" → qna
    - "수입 절차가 궁금해" → qna

    사용자 쿼리: {query}

    반드시 다음 중 하나만 응답하세요: customs_tracking, tariff_prediction, qna
    """
    
    result = llm.invoke([
        SystemMessage(content=classification_prompt.format(query=state["query"]))
    ])
    
    intent = str(result.content).strip()
    if intent not in ["customs_tracking", "tariff_prediction", "qna"]:
        intent = "qna"  # 기본값
    # 타입 힌트에 맞게 Literal로 제한
    state["intent"] = intent  # type: ignore
    state["messages"].append(AIMessage(content=f"의도 분류 완료: {intent}"))
    print(state)  # type: ignore
    return state