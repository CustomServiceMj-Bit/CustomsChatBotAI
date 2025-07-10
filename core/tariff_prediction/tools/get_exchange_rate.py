from langchain_core.tools import tool


@tool
def get_exchange_rate(currency: str) -> str:
    """환율 정보를 조회합니다."""
    # 더미 환율
    rates = {"USD": 1300, "JPY": 9.8, "EUR": 1420, "CNY": 180}
    return f"{currency}/KRW 환율: {rates.get(currency, '정보 없음')}"