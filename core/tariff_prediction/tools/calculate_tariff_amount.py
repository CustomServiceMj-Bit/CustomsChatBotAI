import pandas as pd
import os
from langchain_core.tools import tool
from core.tariff_prediction.tools.get_exchange_rate_info import get_exchange_rate_api

def find_unit(country: str, df: pd.DataFrame) -> str:
    """국가별 통화 단위를 찾습니다."""
    if country in df['country'].unique().tolist():
        result = df[df['country'] == country]['cur_unit'].iloc[0]
        return result
    else:
        return None  # 국가 정보가 없으면 None 반환

def get_tariff_info(hs_code: str, input_country: str, full_tariff_df: pd.DataFrame):
    """주어진 HS코드와 국가명으로, 우선순위에 따라 가장 적합한 관세율 정보를 찾아 반환합니다."""
    EFTA_COUNTRIES = ['스위스', '리히텐슈타인', '아이슬란드', '노르웨이']
    ASEAN_COUNTRIES = [
        '브루나이', '캄보디아', '인도네시아', '라오스', '말레이시아', 
        '미얀마', '필리핀', '싱가포르', '태국', '베트남'
    ]
    EU_COUNTRIES = [
        '오스트리아', '벨기에', '불가리아', '크로아티아', '키프로스', '체코', '덴마크',
        '에스토니아', '핀란드', '프랑스', '독일', '그리스', '헝가리', '아일랜드',
        '이탈리아', '라트비아', '리투아니아', '룩셈부르크', '몰타', '네덜란드',
        '폴란드', '포르투갈', '루마니아', '슬로바키아', '슬로베니아', '스페인', '스웨덴'
    ]

    # 1. HS코드로 전체 데이터프레임에서 관련 규칙을 먼저 필터링합니다.
    item_df = full_tariff_df[full_tariff_df['number'] == hs_code]
    
    if item_df.empty:
        return {'오류': f"HS Code '{hs_code}'를 찾을 수 없습니다."}

    # 2. 검색할 우선순위 목록을 생성합니다.
    search_priority = []
    search_priority.append(input_country) # 1순위: 국가명 직접 일치
    
    if input_country in EU_COUNTRIES:
        search_priority.append('EU 27개국')
    if input_country in EFTA_COUNTRIES:
        search_priority.append('스위스, 리히텐슈타인')
        search_priority.append('EFTA 4개국')
    if input_country in ASEAN_COUNTRIES:
        search_priority.append('아세안 10개국')
    
    search_priority.append('WTO 회원국') # 3순위: WTO
    search_priority.append('모든 국가')   # 4순위: 기본세율
    
    # 3. 우선순위 목록에 따라 순차적으로 tax_rate를 검색합니다.
    for country_category in search_priority:
        result = item_df[item_df['country'] == country_category]
        
        if not result.empty:
            # 첫 번째로 찾은 규칙을 사용합니다.
            matched_row = result.iloc[0]
            
            # 4. 찾은 규칙을 바탕으로 최종 결과를 구성합니다.
            rate = matched_row['tax_rate']
            fta_code = matched_row['fta']
            category = matched_row['category']
            
            # fta 코드(1 또는 2)에 따라 'Yes'/'No' 결정
            fta_status = 'Yes' if fta_code == 2 else 'No'
            
            final_result = {
                '관세율': rate,
                '적용 관세' : category,
                'FTA 적용': fta_status,
                '비고': f"'{country_category}' 조건에 따라 세율이 결정되었습니다."
            }
            return final_result
            
    # 모든 우선순위를 확인했으나 세율을 찾지 못한 경우
    return {'오류': f"HS Code '{hs_code}'에 대한 적용 가능한 관세 규칙을 찾을 수 없습니다."}

def calculate_tax_amount(item_price: float, item_count: int, shipping_cost: float, tax_rate: float, usd_rate: float, situation: str):
    """관세를 계산합니다."""
    # 1) 과세 대상 금액 계산
    total_price = item_price * item_count + shipping_cost

    # 2) 시나리오별 과세 예외
    # 2-1) personal 해외 여행 휴대품 – 600USD 면세
    if situation == '해외체류 중 구매':
        total_price_usd = total_price / usd_rate
        if total_price_usd <= 600:
            return {           # 전액 면세
                'total_price'     : total_price,
                'tax_amount'      : 0,
                'total_price_usd' : total_price_usd,
                'tax_amount_usd'  : 0
            }
    # 2-2) 해외배송 – 관세·부가세 0
    if situation == '해외배송':
        return {
            'total_price'     : total_price,
            'tax_amount'      : 0,
            'total_price_usd' : total_price / usd_rate,
            'tax_amount_usd'  : 0
        }

    # 3) 일반(해외직구) 계산
    tax_amount = total_price * (tax_rate / 100)
    return {
        'total_price'     : total_price,
        'tax_amount'      : tax_amount,
        'total_price_usd' : total_price / usd_rate,
        'tax_amount_usd'  : tax_amount / usd_rate
    }

@tool
def calculate_tariff_amount(product_code: str, value: float, origin_country: str, item_count: int = 1, shipping_cost: float = 0, situation: str = "해외직구") -> str:
    """
    상품의 HS 코드(product_code), 가격(value, 단위: 원), 원산지(origin_country)를 입력받아 예상 관세를 계산합니다.
    실제 관세율 데이터베이스를 사용하여 정확한 관세를 계산합니다.
    """
    try:
        # 데이터 파일 로드
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        tariff_df = pd.read_csv(os.path.join(data_dir, '국가별_관세_적용.csv'), dtype={'number': str})
        currency_df = pd.read_csv(os.path.join(data_dir, '통화별_국가.csv'))
        
        # 관세율 정보 조회
        tariff_info = get_tariff_info(product_code, origin_country, tariff_df)
        
        if '오류' in tariff_info:
            return f"관세율 조회 실패: {tariff_info['오류']}"
        
        # 환율 조회
        if not origin_country or origin_country.strip() == "":
            origin_country = "미국"  # 기본값으로 미국 설정
        
        cur_unit = find_unit(origin_country, currency_df)
        if cur_unit is None:
            return f"환율 정보를 찾을 수 없습니다. 국가: {origin_country}"
        usd_rate = get_exchange_rate_api(cur_unit, situation)
        # 환율이 None이면 더미값(1300.0)으로 대체
        if usd_rate is None:
            usd_rate = 1300.0
        
        # 관세 계산
        tax_info = calculate_tax_amount(value, item_count, shipping_cost, float(tariff_info['관세율']), usd_rate, situation)
        
        # 부가가치세 계산
        VAT = 0
        if situation == '해외직구' and tax_info['tax_amount'] != 0:
            VAT = (tax_info['total_price'] + tax_info['tax_amount']) * 0.1
        
        # 최종 결과
        result = {
            'HS코드': product_code,
            '원산지': origin_country,
            '상품가격': f"{value:,}원",
            '수량': item_count,
            '배송비': f"{shipping_cost:,}원",
            '관세율': f"{tariff_info['관세율']}%",
            '관세금액': f"{tax_info['tax_amount']:,.0f}원",
            '부가가치세': f"{VAT:,.0f}원",
            '총 세금': f"{tax_info['tax_amount'] + VAT:,.0f}원",
            '적용 관세 규칙': tariff_info['적용 관세'],
            'FTA 적용': tariff_info['FTA 적용'],
            '비고': tariff_info['비고']
        }
        
        return f"관세 계산 결과:\n" + "\n".join([f"{k}: {v}" for k, v in result.items()])
        
    except Exception as e:
        return f"관세 계산 중 오류 발생: {str(e)}" 