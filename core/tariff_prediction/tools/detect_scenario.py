from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from core.shared.utils.llm import get_llm
from core.tariff_prediction.constants import VALID_SCENARIOS, SCENARIO_DETECTION, LLM_PROMPT_TEMPLATES

@tool
def detect_scenario_from_input(user_input: str) -> str | None:
    """
    사용자 입력에서 관세 예측 시나리오(해외직구, 해외체류 중 구매, 해외배송)를 자동으로 감지합니다.
    LLM을 사용해 감지합니다.
    """
    try:
        llm = get_llm()
        prompt = LLM_PROMPT_TEMPLATES['detect_scenario'].format(user_input=user_input)
        response = llm.invoke([HumanMessage(content=prompt)])
        result = str(response.content) if hasattr(response, 'content') else str(response)
        
        # LLM 응답 정제
        for cleanup_keyword in SCENARIO_DETECTION['RESPONSE_CLEANUP_KEYWORDS']:
            result = result.replace(cleanup_keyword, "")
        result = result.strip()
        
        for scenario in VALID_SCENARIOS:
            if scenario in result:
                return scenario
        return None
    except Exception:
        return None 