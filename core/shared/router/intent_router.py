from langchain_core.messages import SystemMessage, AIMessage

from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm

def intent_router(state: CustomsAgentState) -> CustomsAgentState:
    """사용자 쿼리의 의도를 분류합니다."""
    llm = get_llm()
    
    classification_prompt = """
    다음 사용자 쿼리를 아래 세 카테고리 중 하나로 분류하세요.

    1. customs_tracking: 운송장, 배송, 통관, 조회, 추적, 배송상태, 위치, 도착, 출고, 통관번호, 운송장번호 등
    2. tariff_prediction: 관세, 세금, 세율, 관세 계산, 관세 예측, 세금 얼마, 관세 얼마, 관세 계산해줘, 관세 예측해줘, 세금 예측, 예상 관세, 뭘 샀어, 뭐 샀어, 샀어, 구매 등
    3. qna: 관세청 정보, 전화번호, 법령, 수입/수출 절차, 일반 안내, 기타 FAQ

    # 예시
    - "관세 예측해줘" → tariff_prediction
    - "관세 계산해줘" → tariff_prediction
    - "이 물건의 세금이 얼마나 나올까?" → tariff_prediction
    - "노트북 샀어" → tariff_prediction
    - "미국에서 뭐 샀어" → tariff_prediction
    - "운송장 번호 123456 어디쯤이야?" → customs_tracking
    - "배송이 어디까지 왔어?" → customs_tracking
    - "통관 진행 상황 알려줘" → customs_tracking
    - "관세청 전화번호 알려줘" → qna
    - "수입 절차가 궁금해" → qna
    - "관세청 홈페이지 알려줘" → qna
    - "관세법 제12조가 뭐야?" → qna

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