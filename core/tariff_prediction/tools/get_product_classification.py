from langchain_core.tools import tool


@tool
def get_product_classification(product_name: str) -> str:
    """상품명으로 HS 코드를 조회합니다."""
    # 더미 분류
    classifications = {
        "스마트폰": "8517.12.00",
        "노트북": "8471.30.00", 
        "의류": "6203.42.00",
        "화장품": "3304.99.00"
    }
    for key in classifications:
        if key in product_name:
            return f"{product_name}의 HS 코드: {classifications[key]}"
    return f"{product_name}의 HS 코드를 찾을 수 없습니다. 정확한 상품명을 입력해주세요."