# 관세 예측 모듈 통합 상수 파일

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

# 시나리오 관련 상수
VALID_SCENARIOS = ['해외직구', '해외체류 중 구매', '해외배송']

# 키워드 관련 상수
OFF_TOPIC_KEYWORDS = [
    '날씨', '음식', '영화', '음악', '운동', '취미', '가족', '친구',
    '일', '학교', '공부', '시험', '여행', '휴가', '주말', '주중',
    '아침', '점심', '저녁', '잠', '병원', '약', '건강', '운동'
]

REMOVE_KEYWORDS = [
    '원', '달러', '엔', '위안', '유로', '만원', '천원', 
    '개', '개씩', '개를', '샀', '구매', '에서', '에서 샀', '에서 구매'
]

CORRECTION_KEYWORDS = ['수정', '잘못', '다시', '틀렸']

SESSION_TERMINATION_KEYWORDS = ['중단', '그만', '취소', '종료']

# 간단한 관세 요청 키워드
SIMPLE_TARIFF_REQUESTS = [
    "관세 계산해줘", "관세 예측해줘", "관세 계산", "관세 예측", 
    "세금 계산해줘", "세금 예측해줘"
]

# 관세 관련 키워드 (탈선 판단용)
TARIFF_CONTEXT_KEYWORDS = [
    '관세', '세금', '통관', 'hs', '코드', '가격', '원', '달러', '엔', '유로'
]

# 기본 환율 정보 (API 실패 시 사용)
DEFAULT_EXCHANGE_RATES = {
    '달러': 1300, 
    '엔': 9, 
    '위안': 180, 
    '유로': 1400
}

# 정규표현식 패턴 상수
PRICE_PATTERNS = [
    r'(\d+)[,\s]*원',
    r'(\d+)[,\s]*달러',
    r'(\d+)[,\s]*엔',
    r'(\d+)[,\s]*위안',
    r'(\d+)[,\s]*유로',
    r'(\d+)[,\s]*만원',
    r'(\d+)[,\s]*천원'
]

QUANTITY_PATTERNS = [
    r'(\d+)[\s]*개',
    r'(\d+)[\s]*개씩',
    r'(\d+)[\s]*개를',
    r'(\d+)[\s]*개 샀',
    r'(\d+)[\s]*개 구매'
]

# 기본값 상수
DEFAULT_COUNTRY = "미국"
DEFAULT_QUANTITY = 1
DEFAULT_SHIPPING_COST = 0
DEFAULT_SESSION_ID = "default_session"

# 입력 예시 상수
INPUT_EXAMPLES = {
    'basic': [
        "미국에서 150만원에 노트북을 샀어요",
        "일본에서 10만원짜리 이어폰을 구매했어요", 
        "독일에서 80만원에 운동화 2켤레를 샀어요"
    ],
    'detailed': [
        "인텔 i7 노트북을 150만원에 미국에서 구매했어요"
    ],
    'scenario': [
        "1번", "해외직구", "여행 중에 샀어요"
    ],
    'selection': [
        "1번", "2번", "3번"
    ]
}

# 안내 메시지 상수
GUIDE_MESSAGES = {
    'input_format': "💡 **다음과 같이 입력해 주세요:**",
    'select_number': "💡 **위 후보 중 하나를 선택해 주세요.**",
    'enter_number': "💡 **번호를 입력해 주세요.**",
    'wrong_number': "**잘못된 번호입니다.**",
    'number_range': "1부터 {max} 사이의 번호를 다시 입력해 주세요.",
    'number_example': "예시: \"1번\", \"2번\", \"3번\" 등",
    'reprediction_hint': "만약 후보가 모두 적합하지 않으면 '코드가 없다', '다시', '재예측' 등으로 입력해 주세요."
}

# 오류 메시지 상수
ERROR_MESSAGES = {
    'no_product_name': "상품명을 알 수 없어 HS 코드 예측을 다시 시도할 수 없습니다. 처음부터 다시 입력해 주세요.",
    'parse_error': "HS 코드 예측 결과를 처리하는 중 오류가 발생했습니다. 다시 시도해 주세요.",
    'prediction_failed': "HS 코드 예측에 실패했습니다. 상품명을 더 구체적으로 입력해 주세요.",
    'reprediction_failed': "HS 코드 예측에 다시 실패했습니다. 상품명을 더 구체적으로 입력해 주세요.",
    'reprediction_error': "HS 코드 재예측 중 오류가 발생했습니다. 다시 시도해 주세요.",

    'input_processing_error': "입력 처리 중 오류가 발생했습니다. 숫자를 입력하거나, 재예측을 원하시면 '다시', '재예측' 등으로 입력해 주세요.",
    'unknown_state': "죄송합니다. 현재 상태를 인식할 수 없습니다. 처음부터 다시 시작하겠습니다.",
    'calculation_failed': "계산 결과를 가져오지 못했습니다.",
    'session_terminated': "관세 계산을 중단하겠습니다. 다른 질문이 있으시면 언제든 말씀해 주세요.",
    'calculation_error': "계산 중 오류가 발생했습니다:"
}

# 수정 안내 메시지 상수
CORRECTION_MESSAGES = {
    'scenario_selection': "어떤 정보를 수정하시겠습니까?\n1. 시나리오\n2. 상품 정보\n3. 처음부터 다시 시작",
    'input_collection': "어떤 정보를 수정하시겠습니까?\n1. 상품묘사\n2. 국가\n3. 가격\n4. 수량\n5. 배송비\n6. 처음부터 다시 시작"
}

# LLM 프롬프트 상수
LLM_PROMPTS = {
    'reprediction_intent': """사용자의 입력이 HS 코드 후보가 적합하지 않아서 재예측을 요청하는 의도인지 판단해주세요.

재예측 의도로 보이는 키워드: "없다", "코드가 없다", "재예측", "다시", "틀렸다", "맞지 않다", "다른", "새로", "다시 예측", "다른 코드", "적합하지 않다"

사용자 입력: {user_input}

위 입력이 재예측을 요청하는 의도인지 판단하여 '네' 또는 '아니오'로만 답변하세요. 반드시 한 단어로만 답변하세요.""",
    
    'hs6_reprediction': """아래 상품명과 사용자의 추가 의견을 참고하여 HS 코드 후보를 예측해주세요.

상품명: {product_name}
사용자 추가 의견: {user_input}

다음 형식으로 HS 코드 후보 3개 이내를 반환하세요:
1. [6자리 HS코드] (확률: [확률]%)
2. [6자리 HS코드] (확률: [확률]%)
3. [6자리 HS코드] (확률: [확률]%)

예시:
1. 851770 (확률: 85.5%)
2. 851712 (확률: 12.3%)
3. 851713 (확률: 2.2%)""",
    
    # 추가 누락된 키들
    'hs6_reprediction_intent': "사용자의 입력이 HS 코드 후보가 적합하지 않아서 재예측을 요청하는 의도인지 판단해주세요.",
    'hs6_reprediction_keywords': '재예측 의도로 보이는 키워드: "없다", "코드가 없다", "재예측", "다시", "틀렸다", "맞지 않다", "다른", "새로", "다시 예측", "다른 코드", "적합하지 않다"',
    'user_input': "사용자 입력",
    'hs6_reprediction_prompt_response': "위 입력이 재예측을 요청하는 의도인지 판단하여 '네' 또는 '아니오'로만 답변하세요. 반드시 한 단어로만 답변하세요.",
    'hs6_reprediction_prompt': "아래 상품명과 사용자의 추가 의견을 참고하여 HS 코드 후보를 예측해주세요.",
    'product_name': "상품명",
    'user_additional_opinion': "사용자 추가 의견",
    'hs6_reprediction_format': "다음 형식으로 HS 코드 후보 3개 이내를 반환하세요:\n1. [6자리 HS코드] (확률: [확률]%)\n2. [6자리 HS코드] (확률: [확률]%)\n3. [6자리 HS코드] (확률: [확률]%)",
    'hs6_reprediction_example': "예시:\n1. 851770 (확률: 85.5%)\n2. 851712 (확률: 12.3%)\n3. 851713 (확률: 2.2%)"
}

# 응답 메시지 상수
RESPONSE_MESSAGES = {
    'input_collection_prompt': """구매하신 상품 정보를 입력해 주세요!

💡 **상품 묘사의 정확도가 높을수록 정확한 관세 예측이 가능합니다!**

💡 **배송비는 따로 입력받고 있지 않습니다. 국제배송비(직배송)는 관세기준에 포함되지 않지만 현지 배송비는 관세기준에 포함되니 참고하시어 상품 가격과 같이 입력 부탁드립니다!**

예시:
• \"아랫창은 고무로 되어있고 하얀색 운동화를 80000원에 독일에서 샀어요\"
• \"인텔 i7 노트북을 150만원에 미국에서 구매했어요\"
• \"블루투스 이어폰 2개를 12만원에 일본에서 샀어요\"

위 예시를 참고하여 상품 정보를 입력해 주세요.""",
    
    'simple_tariff_request': """관세 계산을 위해 다음 정보가 필요합니다:

• 상품명 또는 상품 설명
• 구매 국가
• 상품 가격
• 수량 (선택사항)

💡 **다음과 같이 입력해 주세요:**
• \"미국에서 150만원에 노트북을 샀어요\"
• \"일본에서 10만원짜리 이어폰을 구매했어요\"
• \"독일에서 80만원에 운동화 2켤레를 샀어요\"

위 예시 중 하나를 참고하여 상품 정보를 입력해 주세요.""",
    
    'continue_or_stop': "현재 관세 계산을 진행 중입니다. 계속 진행하시겠습니까, 아니면 중단하시겠습니까?\n\n계속하려면 '계속'을, 중단하려면 '중단'을 입력해 주세요.",
    
    # HS 코드 선택 관련
    'hs6_candidates_header': "HS 코드 예측 모델로부터 HS6 코드 후보를 찾았습니다. 번호를 선택해 주세요:",
    'hs10_candidates_header': "HS 10자리 코드 후보를 선택해 주세요:",
    'selected_hs6_header': "선택하신 HS 6자리 코드: {hs6_code}",
    'hs6_reprediction_header': "HS 코드 재예측 결과입니다. 번호를 선택해 주세요:",
    'hs10_reprediction_header': "HS 10자리 코드 재예측 결과입니다. 번호를 선택해 주세요:",
    
    # 계산 결과 관련
    'calculation_complete': "# 🎯 관세 계산 완료!",
    'product_info_header': "## 📦 상품 정보",
    'calculation_result_header': "## 📊 계산 결과",
    'reference_header': "## 💡 참고사항",
    'reference_content': """- 위 금액은 예상 관세이며, 실제 관세는 세관 심사 결과에 따라 달라질 수 있습니다.
- 정확한 관세는 통관 시 세관에서 최종 결정됩니다.
- 추가 문의사항이 있으시면 언제든 말씀해 주세요!""",
    
    # HS10 선택 관련
    'hs10_no_reprediction': "💡 **번호를 입력해 주세요.** (예: 1, 2, 3)",
    
    # 추가 누락된 키들
    'hs10_reprediction_not_available': "💡 **번호를 입력해 주세요.** (예: 1, 2, 3)",
    'off_topic_warning': "현재 관세 계산을 진행 중입니다. 계속 진행하시겠습니까, 아니면 중단하시겠습니까?\n\n계속하려면 '계속'을, 중단하려면 '중단'을 입력해 주세요.",
    'unrecognized_state': "죄송합니다. 현재 상태를 인식할 수 없습니다. 처음부터 다시 시작하겠습니다.",
    'missing_info_prompt': "다음 정보가 누락되었습니다:",
    'product_info_example': "💡 **상품명, 구매 국가, 상품 가격을 모두 입력해 주세요!**\n\n예시:\n• \"미국에서 150만원에 노트북을 샀어요\"\n• \"일본에서 10만원짜리 이어폰을 구매했어요\"\n• \"독일에서 80만원에 운동화 2켤레를 샀어요\"\n\n위 예시를 참고하여 상품 정보를 입력해 주세요.",
    'scenario_guide_prefix': "예상하고 안내를 도와드릴게요.",
    'scenario_guide_suffix': "",
    'hs6_code_prediction_prompt': "HS 코드 예측 모델로부터 HS6 코드 후보를 찾았습니다. 번호를 선택해 주세요:",
    'hs6_confidence': "신뢰도:",
    'hs6_code_selection_prompt': "💡 **위 후보 중 하나를 선택해 주세요.**",
    'hs6_code_selected': "선택하신 HS 6자리 코드:",
    'hs10_code_prediction_prompt': "HS 10자리 코드 후보를 선택해 주세요:",
    'hs10_code_selection_prompt': "💡 **위 후보 중 하나를 선택해 주세요.**",
    'invalid_number': "**잘못된 번호입니다.**",
    'hs6_code_reprediction_hint': "만약 후보가 모두 적합하지 않으면 '코드가 없다', '다시', '재예측' 등으로 입력해 주세요.",
    'input_processing_error': "입력 처리 중 오류가 발생했습니다. 숫자를 입력하거나, 재예측을 원하시면 '다시', '재예측' 등으로 입력해 주세요.",
    'calculation_result_not_found': "계산 결과를 가져오지 못했습니다.",
    'product_name_not_available': "상품명을 알 수 없어 HS 코드 예측을 다시 시도할 수 없습니다. 처음부터 다시 입력해 주세요.",
    'hs6_code_prediction_failed': "HS 코드 예측에 실패했습니다. 상품명을 더 구체적으로 입력해 주세요.",
    'hs6_code_prediction_processing_error': "HS 코드 예측 결과를 처리하는 중 오류가 발생했습니다. 다시 시도해 주세요.",
    'hs6_code_reprediction_result': "HS 코드 재예측 결과입니다. 번호를 선택해 주세요:",
    'hs6_code_reprediction_error': "HS 코드 재예측 중 오류가 발생했습니다. 다시 시도해 주세요.",
    'hs6_code_not_available': "HS6 코드가 없어 HS10 코드 예측을 다시 시도할 수 없습니다. HS6 코드부터 다시 선택해 주세요.",
    'hs10_code_prediction_failed': "HS10 코드 예측에 실패했습니다. HS6 코드를 다시 선택해 주세요.",
    'hs10_code_reprediction_result': "HS 10자리 코드 재예측 결과입니다. 번호를 선택해 주세요:",
    'hs10_code_reprediction_error': "HS10 코드 재예측 중 오류가 발생했습니다. 다시 시도해 주세요.",
    'product_name_placeholder': "상품",
    'country_placeholder': "해당 국가",
    'scenario_placeholder': "해외직구",
    'tariff_calculation_complete': "관세 계산 완료!",
    'product_info': "상품 정보",
    'calculation_result': "계산 결과",
    'note': "참고사항",
    'tariff_note_1': "위 금액은 예상 관세이며, 실제 관세는 세관 심사 결과에 따라 달라질 수 있습니다.",
    'tariff_note_2': "정확한 관세는 통관 시 세관에서 최종 결정됩니다.",
    'tariff_note_3': "추가 문의사항이 있으시면 언제든 말씀해 주세요!",
    'previous_llm_response': "이전 LLM 응답:"
}

# 상태 관련 상수
STATE_KEYS = {
    'scenario': 'scenario',
    'product_name': 'product_name',
    'country': 'country',
    'price': 'price',
    'quantity': 'quantity',
    'shipping_cost': 'shipping_cost',
    'hs6_code': 'hs6_code',
    'hs10_code': 'hs10_code',
    'current_step': 'current_step',
    'session_active': 'session_active',
    'responses': 'responses',
    'predicted_scenario': 'predicted_scenario',
    'last_user_input': 'last_user_input',
    'hs6_candidates': 'hs6_candidates',
    'hs10_candidates': 'hs10_candidates',
    'price_unit': 'price_unit'
}

# 단계별 상수
STEPS = {
    'scenario_selection': 'scenario_selection',
    'input_collection': 'input_collection',
    'hs6_selection': 'hs6_selection',
    'hs10_selection': 'hs10_selection',
    'input': 'input',
    'hs6_select': 'hs6_select',
    'hs10_select': 'hs10_select'
}

# 디버그 메시지 상수
DEBUG_MESSAGES = {
    'agent_called': "[DEBUG] tariff_prediction_agent called with query: {query}",
    'parse_error': "[DEBUG] parse_hs6_result error: {error}",
    'reprediction_error': "[DEBUG] _perform_hs6_reprediction error: {error}",
    'hs10_reprediction_error': "[DEBUG] _perform_hs10_reprediction error: {error}",
    'llm_classification_error': "[DEBUG] LLM 분류 오류: {error}"
}

# 국가 그룹 상수
COUNTRY_GROUPS = {
    'EFTA_COUNTRIES': ['스위스', '리히텐슈타인', '아이슬란드', '노르웨이'],
    'ASEAN_COUNTRIES': [
        '브루나이', '캄보디아', '인도네시아', '라오스', '말레이시아', 
        '미얀마', '필리핀', '싱가포르', '태국', '베트남'
    ],
    'EU_COUNTRIES': [
        '오스트리아', '벨기에', '불가리아', '크로아티아', '키프로스', '체코', '덴마크',
        '에스토니아', '핀란드', '프랑스', '독일', '그리스', '헝가리', '아일랜드',
        '이탈리아', '라트비아', '리투아니아', '룩셈부르크', '몰타', '네덜란드',
        '폴란드', '포르투갈', '루마니아', '슬로바키아', '슬로베니아', '스페인', '스웨덴'
    ]
}

# VAT 관련 상수
VAT_THRESHOLDS = {
    'US_THRESHOLD': 200,  # 미국 $200 초과 시 VAT 부과
    'OTHER_THRESHOLD': 150,  # 기타 국가 $150 초과 시 VAT 부과
    'VAT_RATE': 0.1  # VAT 세율 10%
}

# 관세 계산 관련 상수
TARIFF_CALCULATION = {
    'PERSONAL_EXEMPTION_LIMIT': 600,  # 해외체류 중 구매 시 면세 한도 (USD)
    'DEFAULT_USD_RATE': 1300.0,  # 기본 USD 환율
    'DEFAULT_COUNTRY': '미국'  # 기본 국가
}

# LLM 프롬프트 템플릿
LLM_PROMPT_TEMPLATES = {
    'clean_product_description': """# 지시문 
다음 입력은 HS코드 분류를 기다리는 제품의 설명입니다.  
HS코드 분류를 위해선 제품에 대한 설명이 명료해야 합니다.  
**명확한 설명**이란 제품의 **기능, 용도, 구성 재질, 작동 방식** 등을 구체적으로 언급하는 것을 의미합니다.  
브랜드명이나 단순 품명만으로는 분류가 어렵습니다.  

# 제약조건
- 브랜드나 품명이 아닌 제품의 기능과 특징에 대해 서술해야 합니다.

# 예시
입력: 전기 모터가 내장되어 있어 회전하는 브러시를 통해 바닥 먼지를 흡입하는 청소기  
출력: result: "바닥 청소를 위해 전기 모터로 구동되는 회전식 브러시가 장착된 가정용 흡입 장치"

입력: 스마트폰과 연동되어 건강 상태를 측정할 수 있는 손목 밴드  
출력: result: "심박수, 걸음 수 등 건강 데이터를 측정하고 스마트폰과 블루투스로 연동되는 전자 손목 밴드"

# 입력  
{item_description}

# 출력
result: "
""",
    
    'parse_user_input': """아래는 관세 예측을 위한 사용자 입력입니다. 입력에서 다음 정보를 추출해 JSON으로 반환하세요.
- product_name: 상품명 또는 상품 설명 (가장 중요한 정보, 반드시 추출해야 함)
- country: 구매 국가 (예: 미국, 일본, 독일 등)
- price: 상품 가격(원화가 아닌 경우 원래 통화 단위 그대로 유지, 숫자만)
- price_unit: 가격 단위 (원, 달러, 엔, 위안, 유로 등)
- quantity: 수량(숫자, 없으면 1)
- shipping_cost: 배송비(숫자, 없으면 0)

입력: "{user_input}"

주의사항:
1. product_name은 반드시 추출해야 합니다. 입력이 "커피"라면 product_name은 "커피"여야 합니다.
2. 입력이 단순한 상품명만 있는 경우에도 product_name을 추출하세요.
3. 가격이나 국가 정보가 없어도 상품명은 반드시 추출하세요.
4. 배송비가 명시되어 있으면 반드시 shipping_cost로 추출하세요.

반환 예시:
{{
  "product_name": "커피",
  "country": null,
  "price": null,
  "price_unit": null,
  "quantity": 1,
  "shipping_cost": 0
}}

또는

{{
  "product_name": "노트북",
  "country": "미국",
  "price": 150,
  "price_unit": "달러",
  "quantity": 1,
  "shipping_cost": 20000
}}

반드시 위와 같은 JSON만 반환하세요.""",
    
    'detect_scenario': """다음은 관세 계산을 위한 사용자 입력입니다. 이 입력이 어떤 시나리오에 해당하는지 판단해주세요.

시나리오 종류:
1. 해외직구: 온라인 쇼핑몰에서 해외 상품을 구매하는 경우
2. 해외체류 중 구매: 해외 여행 중에 직접 구매하여 휴대품으로 가져오는 경우  
3. 해외배송: 해외에서 한국으로 택배나 운송을 통해 배송받는 경우

사용자 입력: "{user_input}"

위 입력을 분석하여 다음 중 하나로 답변해주세요:
- "해외직구"
- "해외체류 중 구매" 
- "해외배송"

답변:""",
    
    'step_classification': """다음 사용자 입력이 관세 예측 플로우의 어떤 단계에 해당하는지 분류하세요.
- 상품 설명 입력: input
- HS6 코드 선택: hs6_select
- HS10 코드 선택 및 관세 계산: hs10_select
반드시 input, hs6_select, hs10_select 중 하나로만 답하세요.
사용자 입력: {user_input}"""
}

# Step API 관련 상수
STEP_API = {
    'AUTO_STEP': 'auto',
    'INPUT_STEP': 'input',
    'HS6_SELECT_STEP': 'hs6_select',
    'HS10_SELECT_STEP': 'hs10_select',
    'RESULT_STEP': 'result',
    'ERROR_KEYWORDS': ['오류', 'Error', '실패'],
    'DEFAULT_ERROR_MESSAGE': '잘못된 요청입니다. 상품 설명을 입력해 주세요.',
    'HS6_SELECTION_MESSAGE': '상품에 해당하는 HS6 코드를 선택해 주세요.',
    'HS10_SELECTION_MESSAGE': 'HS10 코드 후보를 선택해 주세요.'
}

# 관세 결과 파싱 관련 상수
TARIFF_RESULT_PARSING = {
    'FIELD_MAPPINGS': {
        'HS코드:': 'hs_code',
        '원산지:': 'origin_country',
        '상품가격:': 'product_price',
        '수량:': 'quantity',
        '배송비:': 'shipping_cost',
        '관세율:': 'tariff_rate',
        '관세금액:': 'tariff_amount',
        '부가가치세:': 'vat_amount',
        '총 세금:': 'total_tax',
        '적용 관세 규칙:': 'tariff_rule',
        'FTA 적용:': 'fta_applied',
        '비고:': 'note'
    },
    'DEFAULT_VALUES': {
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
        'note': ''
    }
}

# 상품명 추출 관련 상수
PRODUCT_NAME_EXTRACTION = {
    'SIMPLE_PATTERNS': [
        r'^([가-힣a-zA-Z0-9]+)$',  # 단일 단어 (커피, 노트북 등)
        r'^([가-힣a-zA-Z0-9\s]+)$',  # 단일 단어 + 공백
        r'([가-힣a-zA-Z0-9]+)\s*(?:을|를|이|가|의)',  # 조사 앞의 단어
        r'(?:이|가|을|를)\s*([가-힣a-zA-Z0-9]+)',  # 조사 뒤의 단어
    ],
    'REMOVE_KEYWORDS_EXTENDED': [
        '샀어요', '구매', '예측해줘', '관세', '예측', '해줘', '어떻게', '알려줘', '계산', '해주세요'
    ],
    'MIN_LENGTH': 2,
    'MAX_LENGTH': 20
}

# 시나리오 감지 관련 상수
SCENARIO_DETECTION = {
    # LLM 응답 정제 키워드
    'RESPONSE_CLEANUP_KEYWORDS': [
        "답변:", "입니다", "에 해당합니다", ".", "\"", "'"
    ]
} 