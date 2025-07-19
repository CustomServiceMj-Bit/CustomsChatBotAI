import requests
from datetime import datetime
import pandas as pd
import re
from langchain_core.tools import tool
import os

from core.tariff_prediction.constants.api_config import KOREAEXIM_API_URL, KOREAEXIM_API_KEY
from core.tariff_prediction.constants import SUPPORTED_COUNTRIES

def is_supported_country(country: str) -> bool:
    """지원되는 국가인지 확인합니다."""
    return country in SUPPORTED_COUNTRIES

def get_currency_for_country(country: str) -> str:
    """국가에 해당하는 통화를 반환합니다."""
    return SUPPORTED_COUNTRIES.get(country, 'USD')

def get_exchange_rate_api(cur_unit: str, situation: str = '해외직구'):
    """한국수출입은행 API를 사용하여 환율을 조회합니다."""

    today_date = datetime.now().strftime('%Y%m%d')
    
    params = {
        'authkey': KOREAEXIM_API_KEY,
        'searchdate': today_date,
        'data': 'AP01'
    }

    try:
        response = requests.get(KOREAEXIM_API_URL, params=params)
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
        print("환율 api 오류: ",e)
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