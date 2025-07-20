from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from core.shared.utils.llm import get_llm
from core.tariff_prediction.constants import VALID_SCENARIOS

@tool
def detect_scenario_from_input(user_input: str) -> str | None:
    """
    사용자 입력에서 관세 예측 시나리오(해외직구, 해외체류 중 구매, 해외배송)를 자동으로 감지합니다.
    키워드 기반 우선 매칭 후, 실패 시 LLM을 사용해 감지합니다.
    """
    try:
        lowered = user_input.lower()
        # 키워드 기반 우선 매칭
        if any(word in lowered for word in ["여행", "직접", "휴대", "체류"]):
            return "해외체류 중 구매"
        if any(word in lowered for word in ["온라인", "쇼핑", "직구"]):
            return "해외직구"
        if any(word in lowered for word in ["배송", "택배", "운송"]):
            return "해외배송"
        # 키워드 매칭 실패 시 LLM fallback
        llm = get_llm()
        prompt = f"""다음은 관세 계산을 위한 사용자 입력입니다. 이 입력이 어떤 시나리오에 해당하는지 판단해주세요.\n\n시나리오 종류:\n1. 해외직구: 온라인 쇼핑몰에서 해외 상품을 구매하는 경우\n2. 해외체류 중 구매: 해외 여행 중에 직접 구매하여 휴대품으로 가져오는 경우  \n3. 해외배송: 해외에서 한국으로 택배나 운송을 통해 배송받는 경우\n\n사용자 입력: \"{user_input}\"\n\n위 입력을 분석하여 다음 중 하나로 답변해주세요:\n- \"해외직구\"\n- \"해외체류 중 구매\" \n- \"해외배송\"\n\n답변:"""
        response = llm.invoke([HumanMessage(content=prompt)])
        result = str(response.content) if hasattr(response, 'content') else str(response)
        result = result.strip().replace("답변:", "").replace("입니다", "").replace("에 해당합니다", "").replace(".", "").replace("\"", "").replace("'", "").strip()
        for scenario in VALID_SCENARIOS:
            if scenario in result:
                return scenario
        return None
    except Exception:
        return None 