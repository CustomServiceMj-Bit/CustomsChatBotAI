import requests
from datetime import datetime
import pandas as pd
import re
from langchain_core.tools import tool
from core.shared.utils.llm import get_llm
import os

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

def is_supported_country(country: str) -> bool:
    """지원되는 국가인지 확인합니다."""
    return country in SUPPORTED_COUNTRIES

def get_currency_for_country(country: str) -> str:
    """국가에 해당하는 통화를 반환합니다."""
    return SUPPORTED_COUNTRIES.get(country, 'USD')

def get_exchange_rate_api(cur_unit: str, situation: str = '해외직구'):
    """실제 한국수출입은행 API를 사용하여 환율을 조회합니다."""
    url = 'https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON'
    today_date = datetime.now().strftime('%Y%m%d')
    api_key = os.getenv('KOREAEXIM_API_KEY', '')  # 환경변수에서 API 키 가져오기
    
    params = {
        'authkey': api_key,  
        'searchdate': today_date,
        'data': 'AP01'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  
        data = pd.DataFrame(response.json())

        filtered_data = data[data['cur_unit'] == cur_unit]
        if filtered_data.empty:
            raise ValueError(f"Currency {cur_unit} not found in exchange rate data")
            
        if situation == '해외직구' or situation == '해외체류 중 구매':
            usd_rate = filtered_data['ttb'].iloc[0]
        elif situation == '해외배송':
            usd_rate = filtered_data['tts'].iloc[0]
        else:
            raise ValueError("Invalid situation. Use '해외직구' or '해외배송'.")
        
        usd_rate = re.sub(r'(?<=\d),(?=\d)', '', usd_rate)
        usd_rate = float(usd_rate)

        return usd_rate
    except Exception as e:
        return None  # 오류 시 None 반환

@tool
def get_exchange_rate_info(currency: str, situation: str = "해외직구") -> str:
    """실제 환율 정보를 조회합니다. 한국수출입은행 API를 사용합니다."""
    try:
        rate = get_exchange_rate_api(currency, situation)
        if rate is not None:
            return f"{currency}/KRW 환율: {rate:.2f}원 (기준일: {datetime.now().strftime('%Y-%m-%d')})"
        else:
            return f"{currency}/KRW 환율 조회 실패: 환율 정보를 가져올 수 없습니다."
    except Exception as e:
        return f"{currency}/KRW 환율 조회 실패: {str(e)}"

@tool
def check_country_support(country: str) -> str:
    """국가의 환율 지원 여부를 확인합니다."""
    if is_supported_country(country):
        currency = get_currency_for_country(country)
        return f"'{country}'는 지원되는 국가입니다. 통화: {currency}"
    else:
        return f"죄송합니다. '{country}'의 환율 정보는 현재 제공되지 않습니다. 지원되는 국가로 다시 입력해 주세요." 