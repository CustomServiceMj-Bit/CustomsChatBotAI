from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from core.shared.utils.llm import get_llm

@tool
def clean_product_description(item_description: str) -> str:
    """
    제품 설명을 입력받아 HS코드 분류에 적합한 형태로 정리합니다.
    기능, 용도, 구성 재질, 작동 방식 등을 중심으로 명확한 설명을 생성합니다.
    """
    try:
        llm = get_llm()
        
        prompt_template = """
        # 지시문 
        다음 입력은 HS코드 분류를 기다리는 제품의 설명입니다.  
        HS코드 분류를 위해선 제품에 대한 설명이 명료해야 합니다.  
        **명확한 설명**이란 제품의 **기능, 용도, 구성 재질, 작동 방식** 등을 구체적으로 언급하는 것을 의미합니다.  
        브랜드명이나 단순 품명만으로는 분류가 어렵습니다.  

        # 제약조건
        - 브랜드나 품명이 아닌 제품의 기능과 특징에 대해 서술해야 합니다.

        # 예시
        입력: 전기 모터가 내장되어 있어 회전하는 브러시를 통해 바닥 먼지를 흡입하는 청소기  
        출력: result: "바닥 청소를 위해 전기 모터로 구동되는 회전식 브러시가 장착된 가정용 흡입 장치"

        입력: 스마트폰과 연동되어 건강 상태를 측정할 수 있는 손목 밴드  
        출력: result: "심박수, 걸음 수 등 건강 데이터를 측정하고 스마트폰과 블루투스로 연동되는 전자 손목 밴드"

        # 입력  
        {item_description}

        # 출력
        result: "
        """
        
        prompt = prompt_template.format(item_description=item_description)
        
        response = llm.invoke([HumanMessage(content=prompt)])

        result = str(response.content) if hasattr(response, 'content') else str(response)
        return result.strip()

    except Exception as e:
        return item_description  # 실패 시 원본 반환 