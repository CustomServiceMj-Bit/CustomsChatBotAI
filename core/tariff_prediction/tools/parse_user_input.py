from typing import Dict, Any
import re
from langchain_core.tools import tool
from core.shared.utils.llm import get_llm
import json
from core.tariff_prediction.constants import SUPPORTED_COUNTRIES, REMOVE_KEYWORDS, PRICE_PATTERNS, QUANTITY_PATTERNS

def parse_user_input_rule(user_input: str) -> Dict[str, Any]:
    parsed = {}
    
    # 상품명을 먼저 추출 (가장 중요한 정보)
    product_name = extract_product_name(user_input)
    if product_name:
        parsed['product_name'] = product_name
    
    # 가격 정보 추출 (만원, 천원, 원, 달러, 엔, 위안 등)
    price = None
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, user_input)
        if match:
            price_str = match.group(1).replace(',', '')
            unit = match.group(2) if len(match.groups()) > 1 else ''
            try:
                price = float(price_str)
                if '만' in unit:
                    price *= 10000
                elif '천' in unit:
                    price *= 1000
                parsed['price'] = price
                break
            except Exception:
                continue
    
    # 수량 정보 추출 (숫자+개, 한 개, 두 개 등)
    quantity = None
    for pattern in QUANTITY_PATTERNS + [r'([한두세네]) ?개']:
        match = re.search(pattern, user_input)
        if match:
            try:
                if match.group(1).isdigit():
                    quantity = int(match.group(1))
                else:
                    h2n = {'한':1, '두':2, '세':3, '네':4}
                    quantity = h2n.get(match.group(1), 1)
                parsed['quantity'] = quantity
                break
            except Exception:
                continue
    
    # 국가 정보 추출 (미국에서, 일본에서 등 조사 포함)
    country = None
    for c in SUPPORTED_COUNTRIES.keys():
        if c in user_input:
            country = c
            parsed['country'] = c
            break
        elif c + '에서' in user_input:
            country = c
            parsed['country'] = c
            break
    
    return parsed

def extract_product_name(user_input: str) -> str:
    """상품명을 추출하는 전용 함수"""
    # 간단한 상품명 패턴 (단일 단어 또는 짧은 구문)
    simple_patterns = [
        r'^([가-힣a-zA-Z0-9]+)$',  # 단일 단어 (커피, 노트북 등)
        r'^([가-힣a-zA-Z0-9\s]+)$',  # 단일 단어 + 공백
        r'([가-힣a-zA-Z0-9]+)\s*(?:을|를|이|가|의)',  # 조사 앞의 단어
        r'(?:이|가|을|를)\s*([가-힣a-zA-Z0-9]+)',  # 조사 뒤의 단어
    ]
    
    for pattern in simple_patterns:
        match = re.search(pattern, user_input.strip())
        if match:
            product = match.group(1).strip()
            if product and len(product) >= 2:  # 최소 2글자 이상
                return product
    
    # 기존 방식으로 정제
    cleaned = user_input
    for pattern in PRICE_PATTERNS + QUANTITY_PATTERNS + [r'([한두세네]) ?개']:
        cleaned = re.sub(pattern, '', cleaned)
    
    # 국가명 제거
    for c in SUPPORTED_COUNTRIES.keys():
        cleaned = cleaned.replace(c, '')
        cleaned = cleaned.replace(c + '에서', '')
    
    # 불필요한 키워드 제거
    for keyword in REMOVE_KEYWORDS + ['샀어요', '구매', '예측해줘', '관세', '예측', '해줘', '어떻게', '알려줘', '계산', '해주세요']:
        cleaned = cleaned.replace(keyword, '')
    
    cleaned = cleaned.strip()
    
    # 정제된 결과가 있으면 반환
    if cleaned and len(cleaned) >= 2:
        return cleaned
    
    # 마지막 수단: 입력 전체를 상품명으로 사용 (단, 너무 길지 않은 경우)
    if len(user_input.strip()) <= 20 and len(user_input.strip()) >= 2:
        return user_input.strip()
    
    return ""

@tool
def parse_user_input(user_input: str) -> Dict[str, Any]:
    """자연어 입력을 LLM으로 파싱하여 상품 정보를 추출합니다. 실패 시 rule 기반 파싱을 fallback으로 사용합니다."""
    
    # 간단한 입력의 경우 rule 기반 파싱을 우선 사용
    if len(user_input.strip()) <= 10:
        rule_result = parse_user_input_rule(user_input)
        if rule_result.get('product_name'):
            return rule_result
    
    prompt = f"""
아래는 관세 예측을 위한 사용자 입력입니다. 입력에서 다음 정보를 추출해 JSON으로 반환하세요.
- product_name: 상품명 또는 상품 설명 (가장 중요한 정보, 반드시 추출해야 함)
- country: 구매 국가 (예: 미국, 일본, 독일 등)
- price: 상품 가격(원화가 아닌 경우 원래 통화 단위 그대로 유지, 숫자만)
- price_unit: 가격 단위 (원, 달러, 엔, 위안, 유로 등)
- quantity: 수량(숫자, 없으면 1)

입력: "{user_input}"

주의사항:
1. product_name은 반드시 추출해야 합니다. 입력이 "커피"라면 product_name은 "커피"여야 합니다.
2. 입력이 단순한 상품명만 있는 경우에도 product_name을 추출하세요.
3. 가격이나 국가 정보가 없어도 상품명은 반드시 추출하세요.

반환 예시:
{{
  "product_name": "커피",
  "country": null,
  "price": null,
  "price_unit": null,
  "quantity": 1
}}

또는

{{
  "product_name": "노트북",
  "country": "미국",
  "price": 150,
  "price_unit": "달러",
  "quantity": 1
}}

반드시 위와 같은 JSON만 반환하세요.
"""
    try:
        llm = get_llm()
        response = llm.invoke([{"role": "user", "content": prompt}])
        json_str = response.content if hasattr(response, 'content') else str(response)
        if not isinstance(json_str, str):
            raise ValueError('LLM 응답이 문자열이 아님')
        json_start = json_str.find('{')
        json_end = json_str.rfind('}') + 1
        parsed = json.loads(json_str[json_start:json_end])
        # product_name이 있으면 반환 (가장 중요한 정보)
        if parsed and parsed.get('product_name'):
            return parsed
    except Exception:
        pass
    
    # 실패 시 rule 기반 파싱
    rule_result = parse_user_input_rule(user_input)
    
    # rule 기반 파싱에서도 product_name이 없으면 입력 전체를 상품명으로 사용
    if not rule_result.get('product_name') and user_input.strip():
        rule_result['product_name'] = user_input.strip()
    
    return rule_result 