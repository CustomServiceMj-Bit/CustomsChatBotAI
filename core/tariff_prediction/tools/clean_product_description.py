from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from core.shared.utils.llm import get_llm
from core.tariff_prediction.constants import LLM_PROMPT_TEMPLATES

@tool
def clean_product_description(item_description: str) -> str:
    """
    제품 설명을 입력받아 HS코드 분류에 적합한 형태로 정리합니다.
    기능, 용도, 구성 재질, 작동 방식 등을 중심으로 명확한 설명을 생성합니다.
    """
    try:
        llm = get_llm()
        
        prompt_template = LLM_PROMPT_TEMPLATES['clean_product_description']
        
        prompt = prompt_template.format(item_description=item_description)
        
        response = llm.invoke([HumanMessage(content=prompt)])

        result = str(response.content) if hasattr(response, 'content') else str(response)
        return result.strip()

    except Exception as e:
        return item_description  # 실패 시 원본 반환 