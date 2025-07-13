from typing import Dict, Any
import re
from langchain_core.tools import tool

# 환율 지원 국가 목록
SUPPORTED_COUNTRIES = {
    '미국': 'USD', '일본': 'JPY', '유럽연합': 'EUR', '중국': 'CNY',
    '독일': 'EUR', '프랑스': 'EUR', '이탈리아': 'EUR', '스페인': 'EUR',
    '네덜란드': 'EUR', '벨기에': 'EUR', '오스트리아': 'EUR', '그리스': 'EUR',
    '포르투갈': 'EUR', '아일랜드': 'EUR', '핀란드': 'EUR', '룩셈부르크': 'EUR',
    '스웨덴': 'EUR', '덴마크': 'EUR', '폴란드': 'EUR', '체코': 'EUR',
    '헝가리': 'EUR', '슬로바키아': 'EUR', '슬로베니아': 'EUR', '에스토니아': 'EUR',
    '라트비아': 'EUR', '리투아니아': 'EUR', '몰타': 'EUR', '키프로스': 'EUR',
    '크로아티아': 'EUR', '루마니아': 'EUR', '불가리아': 'EUR'
}

@tool
def parse_user_input(user_input: str) -> Dict[str, Any]:
    """자연어 입력을 파싱하여 상품 정보를 추출합니다."""
    parsed = {}
    
    # 가격 정보 추출 (숫자 + 원/달러/엔/위안 등)
    price_patterns = [
        r'(\d+)[,\s]*원',
        r'(\d+)[,\s]*달러',
        r'(\d+)[,\s]*엔',
        r'(\d+)[,\s]*위안',
        r'(\d+)[,\s]*유로',
        r'(\d+)[,\s]*만원',
        r'(\d+)[,\s]*천원'
    ]
    
    for pattern in price_patterns:
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
    quantity_patterns = [
        r'(\d+)[\s]*개',
        r'(\d+)[\s]*개씩',
        r'(\d+)[\s]*개를',
        r'(\d+)[\s]*개 샀',
        r'(\d+)[\s]*개 구매'
    ]
    
    for pattern in quantity_patterns:
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
    for pattern in price_patterns + quantity_patterns:
        cleaned_input = re.sub(pattern, '', cleaned_input)
    
    for country in countries:
        cleaned_input = cleaned_input.replace(country, '')
    
    # 일반적인 키워드 제거
    remove_keywords = ['원', '달러', '엔', '위안', '유로', '만원', '천원', '개', '개씩', '개를', '샀', '구매', '에서', '에서 샀', '에서 구매']
    for keyword in remove_keywords:
        cleaned_input = cleaned_input.replace(keyword, '')
    
    # 상품 묘사로 사용할 부분 추출
    cleaned_input = cleaned_input.strip()
    if cleaned_input and len(cleaned_input) > 2:  # 의미있는 길이인 경우만
        parsed['product_name'] = cleaned_input
    
    return parsed 