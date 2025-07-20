from typing import List, Dict
import re
import pandas as pd
import os
from langchain_core.tools import tool

@tool
def parse_hs6_result(hs6_result: str) -> List[Dict]:
    """HS6 결과를 파싱합니다."""
    candidates = []
    # HS6.csv 파일 로드
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    hs6_df = pd.read_csv(os.path.join(data_dir, 'HS6.csv'), dtype={'HS코드': str})
    
    # 결과에서 HS 코드와 확률 추출
    lines = hs6_result.strip().split('\n')
    for line in lines:
        if line.strip() and any(char.isdigit() for char in line):
            # "1. 851770 (확률: 98.02%)" 형태 파싱
            match = re.search(r'(\d+)\.\s*([0-9]{6})\s*\(확률:\s*([0-9.]+)%\)', line)
            if match:
                rank = int(match.group(1))
                code = match.group(2)
                confidence = round(float(match.group(3)) / 100.0, 3)
                hs6_code = code[:4] + '.' + code[4:]
                # HS6.csv에서 정보 찾기
                hs6_row = hs6_df[hs6_df['HS코드'] == code]
                search_text = ""
                if not hs6_row.empty:
                    search_text = str(hs6_row.iloc[0]['검색텍스트'])
                candidates.append({
                    'code': code,  # 포맷팅 없이 원본 6자리 코드 사용
                    'description': f'HS코드: {code}, 설명: {search_text}',
                    'confidence': confidence,
                    'full_code': code
                })
    print(f"[DEBUG] parse_hs6_result candidates: {candidates}")
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