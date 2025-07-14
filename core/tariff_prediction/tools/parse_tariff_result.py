from typing import Dict, Any
from langchain_core.tools import tool

@tool
def parse_tariff_result(tariff_result: str) -> Dict[str, Any]:
    """관세 계산 결과를 파싱하고 포맷팅합니다."""
    parsed = {
        'tariff_rate': '0%',
        'tariff_amount': '0원',
        'vat_amount': '0원',
        'total_tax': '0원',
        'fta_applied': 'No',
        'formatted_result': tariff_result
    }
    
    try:
        # 결과에서 주요 정보 추출
        lines = tariff_result.split('\n')
        for line in lines:
            line = line.strip()
            if '관세율:' in line:
                parsed['tariff_rate'] = line.split(':')[-1].strip()
            elif '관세금액:' in line:
                parsed['tariff_amount'] = line.split(':')[-1].strip()
            elif '부가가치세:' in line:
                parsed['vat_amount'] = line.split(':')[-1].strip()
            elif '총 세금:' in line:
                parsed['total_tax'] = line.split(':')[-1].strip()
            elif 'FTA 적용:' in line:
                parsed['fta_applied'] = line.split(':')[-1].strip()
        
        # 마크다운 형식의 결과 포맷팅
        if parsed['tariff_amount'] != '0원':
            formatted_result = f"""| 항목 | 금액 |
|------|------|
| **관세율** | {parsed['tariff_rate']} |
| **관세금액** | {parsed['tariff_amount']} |
| **부가가치세** | {parsed['vat_amount']} |
| **총 세금** | {parsed['total_tax']} |
| **FTA 적용** | {parsed['fta_applied']} |"""
        else:
            formatted_result = f"""| 항목 | 금액 |
|------|------|
| **관세금액** | {parsed['tariff_amount']} (면세) |
| **부가가치세** | {parsed['vat_amount']} |
| **총 세금** | {parsed['total_tax']} |
| **FTA 적용** | {parsed['fta_applied']} |"""
        
        parsed['formatted_result'] = formatted_result
        
    except Exception as e:
        # 파싱 실패 시 원본 결과 사용
        parsed['formatted_result'] = f"```\n{tariff_result}\n```"
    
    return parsed 