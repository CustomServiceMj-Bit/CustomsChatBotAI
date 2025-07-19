from typing import Dict, Any
import re

def extract_llm_response(response) -> str:
    """LLM 응답을 안전하게 추출합니다."""
    try:
        if hasattr(response, 'content'):
            return str(response.content).strip()
        elif isinstance(response, str):
            return response.strip()
        elif isinstance(response, list) and response:
            return str(response[0]).strip()
        elif isinstance(response, dict):
            return str(response).strip()
        else:
            return str(response).strip()
    except Exception:
        return ""

def extract_info_from_context(context: str) -> Dict[str, str]:
    """컨텍스트에서 상품 정보를 추출합니다."""
    extracted_info = {}
    
    # 상품명 추출 (가장 긴 명사구 찾기)
    product_patterns = [
        r'상품명[:\s]*([^\n]+)',
        r'상품[:\s]*([^\n]+)',
        r'([가-힣a-zA-Z0-9\s]{3,}?)(?:을|를|이|가)\s*(?:샀|구매|구입)',
    ]
    
    for pattern in product_patterns:
        match = re.search(pattern, context)
        if match:
            product_name = match.group(1).strip()
            if len(product_name) > 2:  # 최소 3글자 이상
                extracted_info['product_name'] = product_name
                break
    
    # 국가 추출
    country_patterns = [
        r'국가[:\s]*([^\n]+)',
        r'([가-힣]{2,4})(?:에서|에서\s*샀|에서\s*구매)',
    ]
    
    for pattern in country_patterns:
        match = re.search(pattern, context)
        if match:
            country = match.group(1).strip()
            if len(country) >= 2:
                extracted_info['country'] = country
                break
    
    # 가격 추출
    price_patterns = [
        r'가격[:\s]*([^\n]+)',
        r'(\d+[,\d]*)\s*(?:원|달러|엔|위안|유로)',
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, context)
        if match:
            price = match.group(1).strip()
            extracted_info['price'] = price
            break
    
    # 수량 추출
    quantity_patterns = [
        r'수량[:\s]*(\d+)',
        r'(\d+)\s*개',
    ]
    
    for pattern in quantity_patterns:
        match = re.search(pattern, context)
        if match:
            quantity = match.group(1).strip()
            extracted_info['quantity'] = quantity
            break
    
    return extracted_info

def merge_context_with_current(context_info: Dict[str, str], current_input: str) -> str:
    """컨텍스트 정보와 현재 입력을 병합합니다."""
    merged_input = current_input
    
    # 현재 입력에 없는 정보를 컨텍스트에서 보완
    if 'product_name' in context_info and '상품' not in current_input.lower():
        merged_input = f"{context_info['product_name']} {merged_input}"
    
    if 'country' in context_info and '에서' not in current_input:
        merged_input = f"{context_info['country']}에서 {merged_input}"
    
    if 'price' in context_info and not re.search(r'\d+', current_input):
        merged_input = f"{merged_input} {context_info['price']}"
    
    if 'quantity' in context_info and '개' not in current_input:
        merged_input = f"{merged_input} {context_info['quantity']}개"
    
    return merged_input 