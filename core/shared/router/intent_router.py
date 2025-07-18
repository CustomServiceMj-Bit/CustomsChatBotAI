from langchain_core.messages import SystemMessage, AIMessage

from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm

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
            if any(keyword in content for keyword in [
                'hs6 코드 후보', 'hs10 코드 후보', '번호를 선택', '관세 계산', '관세 예측',
                '상품묘사', '구매 국가', '상품 가격', '시나리오 선택', 'tariff_prediction'
            ]):
                is_in_tariff_session = True
                break
    
    # 이전 의도가 tariff_prediction이었는지도 확인
    if messages and len(messages) > 0:
        last_msg = messages[-1]
        if hasattr(last_msg, 'content') and isinstance(last_msg.content, str):
            if 'tariff_prediction' in last_msg.content:
                is_in_tariff_session = True
    
    # 현재 쿼리가 숫자 선택인지 확인
    current_query = state["query"].strip()
    is_number_selection = False
    
    # 숫자 선택 패턴 확인 (1번, 2번, 3번, 1, 2, 3 등)
    import re
    number_patterns = [
        r'^\d+번?$',  # 1번, 2번, 3번
        r'^\d+$',     # 1, 2, 3
        r'^\d+\.?\d*$',  # 8471.60, 8517.70 등 HS 코드
        r'^\d{4,6}$',  # 8471, 851770 등 HS 코드
        r'^\d{4}\.\d{2}$',  # 8471.60 등 HS 코드
    ]
    
    for pattern in number_patterns:
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
    
    # 일반적인 의도 분류
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
    
    state["intent"] = intent  # type: ignore
    state["messages"].append(AIMessage(content=f"의도 분류 완료: {intent}"))
    print(state)
    return state