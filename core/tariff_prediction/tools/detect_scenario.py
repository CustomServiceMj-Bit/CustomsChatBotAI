from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from core.shared.utils.llm import get_llm
from core.tariff_prediction.constants import VALID_SCENARIOS

@tool
def detect_scenario_from_input(user_input: str) -> str | None:
    """사용자 입력에서 시나리오를 자동 감지합니다."""
    try:
        llm = get_llm()
        prompt = f"""다음은 관세 계산을 위한 사용자 입력입니다. 이 입력이 어떤 시나리오에 해당하는지 판단해주세요.

시나리오 종류:
1. 해외직구: 온라인 쇼핑몰에서 해외 상품을 구매하는 경우
2. 해외체류 중 구매: 해외 여행 중에 직접 구매하여 휴대품으로 가져오는 경우  
3. 해외배송: 해외에서 한국으로 택배나 운송을 통해 배송받는 경우

사용자 입력: "{user_input}"

위 입력을 분석하여 다음 중 하나로 답변해주세요:
- "해외직구"
- "해외체류 중 구매" 
- "해외배송"

답변:"""
        response = llm.invoke([HumanMessage(content=prompt)])
        result = str(response.content) if hasattr(response, 'content') else str(response)
        result = result.strip()
        
        # 응답에서 시나리오 추출 (따옴표나 "답변:" 등의 접두사 제거)
        
        # 직접 매칭 시도
        if result in VALID_SCENARIOS:
            return result
            
        # 응답에서 시나리오 추출 시도
        for scenario in VALID_SCENARIOS:
            if scenario in result:
                return scenario
                
        # "답변:" 접두사 제거 후 시도
        if result.startswith('답변:'):
            clean_result = result.replace('답변:', '').strip().strip('"').strip("'")
            if clean_result in VALID_SCENARIOS:
                return clean_result
                
        return None
    except Exception:
        return None 