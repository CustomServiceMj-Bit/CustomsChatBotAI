from typing import Dict, Any
from langchain_core.tools import tool
from core.tariff_prediction.constants import TARIFF_RESULT_PARSING

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
    parsed = TARIFF_RESULT_PARSING['DEFAULT_VALUES'].copy()
    parsed['formatted_result'] = tariff_result
    
    try:
        # 결과에서 주요 정보 추출
        lines = tariff_result.split('\n')
        for line in lines:
            line = line.strip()
            for field_key, field_name in TARIFF_RESULT_PARSING['FIELD_MAPPINGS'].items():
                if field_key in line:
                    parsed[field_name] = line.split(':')[-1].strip()
                    break
        
        # 가격 포맷팅
        formatted_price = format_price(parsed['product_price'])
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
| **비고** | {parsed['note']} |

---

**본 답변은 신청자가 제시한 자료만을 근거로 작성하였으며, 법적 효력을 갖는 유권해석(결정, 판단)이 아니므로 각종 신고, 불복청구 등의 증거자료로 사용할 수 없습니다.**"""
        
        parsed['formatted_result'] = formatted_result
        
    except Exception as e:
        # 파싱 실패 시 원본 결과를 포맷팅
        formatted_result = f"""## 📊 관세 계산 결과

```
{tariff_result}
```"""
        parsed['formatted_result'] = formatted_result
    
    return parsed 