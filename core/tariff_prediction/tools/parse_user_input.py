from typing import Dict, Any
import re
from langchain_core.tools import tool
from core.shared.utils.llm import get_llm
import json
from core.tariff_prediction.constants import (
    SUPPORTED_COUNTRIES, REMOVE_KEYWORDS, PRICE_PATTERNS, QUANTITY_PATTERNS,
    LLM_PROMPT_TEMPLATES, PRODUCT_NAME_EXTRACTION
)

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
    # 간단한 상품명 패턴 
    simple_patterns = PRODUCT_NAME_EXTRACTION['SIMPLE_PATTERNS']
    
    for pattern in simple_patterns:
        match = re.search(pattern, user_input.strip())
        if match:
            product = match.group(1).strip()
            if product and len(product) >= PRODUCT_NAME_EXTRACTION['MIN_LENGTH']:
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
    for keyword in REMOVE_KEYWORDS + PRODUCT_NAME_EXTRACTION['REMOVE_KEYWORDS_EXTENDED']:
        cleaned = cleaned.replace(keyword, '')
    
    cleaned = cleaned.strip()
    
    # 정제된 결과가 있으면 반환
    if cleaned and len(cleaned) >= PRODUCT_NAME_EXTRACTION['MIN_LENGTH']:
        return cleaned
    
    # 입력 전체를 상품명으로 사용
    if len(user_input.strip()) <= PRODUCT_NAME_EXTRACTION['MAX_LENGTH'] and len(user_input.strip()) >= PRODUCT_NAME_EXTRACTION['MIN_LENGTH']:
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
    
    prompt = LLM_PROMPT_TEMPLATES['parse_user_input'].format(user_input=user_input)
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