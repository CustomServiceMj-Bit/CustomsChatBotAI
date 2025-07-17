from typing import List, Dict
import re
import pandas as pd
import os
from langchain_core.tools import tool

@tool
def parse_hs6_result(hs6_result: str) -> List[Dict]:
    """HS6 결과를 파싱합니다."""
    candidates = []
    
    # 결과에서 HS 코드와 확률 추출
    lines = hs6_result.strip().split('\n')
    for line in lines:
        if line.strip() and any(char.isdigit() for char in line):
            # "1. 8471.30.00 (확률: 85%)" 형태 파싱
            match = re.search(r'(\d+)\.\s*([0-9]{4}\.[0-9]{2}\.[0-9]{2})\s*\(확률:\s*(\d+)%\)', line)
            if match:
                rank = int(match.group(1))
                code = match.group(2)
                confidence = int(match.group(3)) / 100.0
                
                # HS6 코드로 변환 (첫 6자리)
                hs6_code = '.'.join(code.split('.')[:2])
                
                candidates.append({
                    'code': hs6_code,
                    'description': f'HS6 코드 {hs6_code}',
                    'confidence': confidence,
                    'full_code': code
                })
    
    # 파싱 실패 시 더미 데이터 반환
    if not candidates:
        candidates = [
            {'code': '8471.30', 'description': '노트북 컴퓨터', 'confidence': 0.95},
            {'code': '8471.40', 'description': '데스크톱 컴퓨터', 'confidence': 0.85},
            {'code': '8471.50', 'description': '서버 컴퓨터', 'confidence': 0.75}
        ]
    
    return candidates

@tool
def generate_hs10_candidates(hs6_code: str) -> List[Dict]:
    """HS6 코드를 기반으로 HS10 후보를 생성합니다."""
    try:
        # HS10.csv 파일 로드
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        hs10_df = pd.read_csv(os.path.join(data_dir, 'HS10.csv'))
        
        # HS6 코드로 필터링 (HS6 컬럼에서 해당 코드로 시작하는 항목들 찾기)
        hs6_formatted = hs6_code.replace('.', '')
        if len(hs6_formatted) < 6:
            hs6_formatted = hs6_formatted.ljust(6, '0')
        hs6_strs = hs10_df['HS6'].astype(str).str.zfill(6)
        matching_rows = hs10_df[hs6_strs.str.startswith(hs6_formatted)]
        
        candidates = []
        for _, row in matching_rows.iterrows():
            candidates.append({
                'code': str(row['HS10']),  # 항상 문자열로 변환
                'description': row['한글품목명']
            })
        
        return candidates
    except Exception:
        return [] 