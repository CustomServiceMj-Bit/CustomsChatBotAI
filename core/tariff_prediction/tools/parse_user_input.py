from typing import Dict, Any
import re
from langchain_core.tools import tool

from core.tariff_prediction.constants import SUPPORTED_COUNTRIES, REMOVE_KEYWORDS, PRICE_PATTERNS, QUANTITY_PATTERNS

@tool
def parse_user_input(user_input: str) -> Dict[str, Any]:
    """자연어 입력을 파싱하여 상품 정보를 추출합니다."""
    parsed = {}
    
    # 가격 정보 추출 (숫자 + 원/달러/엔/위안 등)
    for pattern in PRICE_PATTERNS:
        matches = re.findall(pattern, user_input)
        if matches:
            price_str = matches[0].replace(',', '')
            if '만원' in user_input:
                parsed['price'] = float(price_str) * 10000
            elif '천원' in user_input:
                parsed['price'] = float(price_str) * 1000
            else:
                parsed['price'] = float(price_str)
            break
    
    # 수량 정보 추출
    for pattern in QUANTITY_PATTERNS:
        matches = re.findall(pattern, user_input)
        if matches:
            parsed['quantity'] = int(matches[0])
            break
    
    # 국가 정보 추출
    countries = list(SUPPORTED_COUNTRIES.keys())
    for country in countries:
        if country in user_input:
            parsed['country'] = country
            break
    
    # 상품 묘사 추출 (가격, 수량, 국가 정보를 제외한 나머지 부분)
    # 먼저 가격, 수량, 국가 관련 키워드를 제거
    cleaned_input = user_input
    for pattern in PRICE_PATTERNS + QUANTITY_PATTERNS:
        cleaned_input = re.sub(pattern, '', cleaned_input)
    
    for country in countries:
        cleaned_input = cleaned_input.replace(country, '')
    
    # 일반적인 키워드 제거
    for keyword in REMOVE_KEYWORDS:
        cleaned_input = cleaned_input.replace(keyword, '')
    
    # 상품 묘사로 사용할 부분 추출
    cleaned_input = cleaned_input.strip()
    if cleaned_input and len(cleaned_input) > 2:  # 의미있는 길이인 경우만
        parsed['product_name'] = cleaned_input
    
    return parsed 