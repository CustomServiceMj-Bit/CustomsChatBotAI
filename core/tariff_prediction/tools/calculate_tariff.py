from langchain_core.tools import tool


@tool
def calculate_tariff(product_code: str, value: float, origin_country: str) -> str:
    """
    상품의 HS 코드(product_code), 가격(value, 단위: USD), 원산지(origin_country)를 입력받아 예상 관세를 계산합니다.
    예: product_code='8471.30.00', value=1500, origin_country='Japan'
    """
    # 더미 계산
    base_rate = 0.08  # 8% 기본 관세율
    calculated_tariff = value * base_rate
    return f"상품코드 {product_code}, 가격 ${value}, 원산지 {origin_country}의 예상 관세: ${calculated_tariff:.2f}"