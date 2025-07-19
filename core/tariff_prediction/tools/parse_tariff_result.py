from typing import Dict, Any
from langchain_core.tools import tool

def format_price(price_str: str) -> str:
    """가격을 깔끔하게 포맷팅합니다."""
    try:
        # 숫자 부분만 추출
        price_str = price_str.replace('원', '').replace(',', '').strip()
        price = float(price_str)
        
        # 정수인 경우 정수로, 소수인 경우 소수점 2자리까지
        if price.is_integer():
            return f"{int(price):,}원"
        else:
            return f"{price:,.2f}원"
    except:
        return price_str

@tool
def parse_tariff_result(tariff_result: str) -> Dict[str, Any]:
    """관세 계산 결과를 파싱하고 포맷팅합니다."""
    parsed = {
        'hs_code': '',
        'origin_country': '',
        'product_price': '',
        'quantity': '',
        'shipping_cost': '',
        'tariff_rate': '0%',
        'tariff_amount': '0원',
        'vat_amount': '0원',
        'total_tax': '0원',
        'tariff_rule': '',
        'fta_applied': 'No',
        'note': '',
        'formatted_result': tariff_result
    }
    
    try:
        # 결과에서 주요 정보 추출
        lines = tariff_result.split('\n')
        for line in lines:
            line = line.strip()
            if 'HS코드:' in line:
                parsed['hs_code'] = line.split(':')[-1].strip()
            elif '원산지:' in line:
                parsed['origin_country'] = line.split(':')[-1].strip()
            elif '상품가격:' in line:
                parsed['product_price'] = line.split(':')[-1].strip()
            elif '수량:' in line:
                parsed['quantity'] = line.split(':')[-1].strip()
            elif '배송비:' in line:
                parsed['shipping_cost'] = line.split(':')[-1].strip()
            elif '관세율:' in line:
                parsed['tariff_rate'] = line.split(':')[-1].strip()
            elif '관세금액:' in line:
                parsed['tariff_amount'] = line.split(':')[-1].strip()
            elif '부가가치세:' in line:
                parsed['vat_amount'] = line.split(':')[-1].strip()
            elif '총 세금:' in line:
                parsed['total_tax'] = line.split(':')[-1].strip()
            elif '적용 관세 규칙:' in line:
                parsed['tariff_rule'] = line.split(':')[-1].strip()
            elif 'FTA 적용:' in line:
                parsed['fta_applied'] = line.split(':')[-1].strip()
            elif '비고:' in line:
                parsed['note'] = line.split(':')[-1].strip()
        
        # 가격 포맷팅
        formatted_price = format_price(parsed['product_price'])
        formatted_shipping = format_price(parsed['shipping_cost'])
        formatted_tariff = format_price(parsed['tariff_amount'])
        formatted_vat = format_price(parsed['vat_amount'])
        formatted_total = format_price(parsed['total_tax'])
        
        # 마크다운 형식의 결과 포맷팅
        formatted_result = f"""## 📊 관세 계산 결과

### 📦 상품 정보
| 항목 | 내용 |
|------|------|
| **HS 코드** | `{parsed['hs_code']}` |
| **원산지** | {parsed['origin_country']} |
| **상품 가격** | {formatted_price} |
| **수량** | {parsed['quantity']}개 |
| **배송비** | {formatted_shipping} |

### 💰 세금 정보
| 항목 | 금액 |
|------|------|
| **관세율** | {parsed['tariff_rate']} |
| **관세금액** | {formatted_tariff} |
| **부가가치세** | {formatted_vat} |
| **총 세금** | **{formatted_total}** |

### 📋 추가 정보
| 항목 | 내용 |
|------|------|
| **적용 관세 규칙** | {parsed['tariff_rule']} |
| **FTA 적용** | {parsed['fta_applied']} |
| **비고** | {parsed['note']} |"""
        
        parsed['formatted_result'] = formatted_result
        
    except Exception as e:
        # 파싱 실패 시 원본 결과를 예쁘게 포맷팅
        formatted_result = f"""## 📊 관세 계산 결과

```
{tariff_result}
```"""
        parsed['formatted_result'] = formatted_result
    
    return parsed 