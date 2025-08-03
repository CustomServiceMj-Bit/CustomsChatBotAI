# Shared constants for the entire application

# 관세 예측 관련 키워드
TARIFF_PREDICTION_KEYWORDS = [
    '코드', 'hs', '관세', '세금', '세율', '관세 계산', '관세 예측', '세금 얼마', '관세 얼마',
    '관세 계산해줘', '관세 예측해줘', '세금 예측', '예상 관세', '뭘 샀어', '뭐 샀어', '샀어', '구매',
    '저기에', '저기', '그곳에', '그곳', '여기에', '여기', '저기에는', '그곳에는', '여기에는',
    '적합하지', '맞지', '틀렸', '잘못', '다른 것', '다른 코드', '새로운', '새로', '다시', '재시도'
]

# 배송 추적 관련 키워드
CUSTOMS_TRACKING_KEYWORDS = [
    '운송장', '통관', '조회', '추적', '배송상태', '위치', '도착', '출고', '통관번호', '운송장번호',
    '통관 진행', '배송 조회', '운송 조회', '통관 조회', '배송 상태', '운송 상태'
]

# 의도 분류 관련 상수들

# 관세 예측 세션 관련 키워드
TARIFF_SESSION_KEYWORDS = [
    'hs6 코드 후보', 'hs10 코드 후보', '번호를 선택', '관세 계산', '관세 예측',
    '상품묘사', '구매 국가', '상품 가격', '시나리오 선택', 'tariff_prediction',
    '해외직구로 예상하고 안내를 도와드릴게요', '선택하신 hs', 'hs 10자리 코드 후보'
]

# 숫자 선택 패턴 (HS 코드, 번호 선택 등)
NUMBER_SELECTION_PATTERNS = [
    r'^\d+번?$',  # 1번, 2번, 3번
    r'^\d+$',     # 1, 2, 3
    r'^\d+\.?\d*$',  # 8471.60, 8517.70 등 HS 코드
    r'^\d{4,6}$',  # 8471, 851770 등 HS 코드
    r'^\d{4}\.\d{2}$',  # 8471.60 등 HS 코드
]

# 질문 형태 감지 패턴
QUESTION_PATTERNS = [
    r'\?$',  # 물음표로 끝나는 경우
    r'^어떻게', r'^무엇', r'^언제', r'^어디서', r'^왜', r'^누가',
    r'^무슨', r'^어떤', r'^얼마나', r'^어디', r'^언제', r'^왜',
    r'알려줘', r'알려주세요', r'궁금해', r'궁금합니다'
]

# 의도 분류 프롬프트
INTENT_CLASSIFICATION_PROMPT = """
다음 사용자 쿼리를 아래 세 카테고리 중 하나로 분류하세요.

1. customs_tracking: 운송장, 배송, 통관, 조회, 추적, 배송상태, 위치, 도착, 출고, 통관번호, 운송장번호 등
2. tariff_prediction: 관세, 세금, 세율, 관세 계산, 관세 예측, 세금 얼마, 관세 얼마, 관세 계산해줘, 관세 예측해줘, 세금 예측, 예상 관세, 뭘 샀어, 뭐 샀어, 샀어, 구매 등
3. qna: 관세청 정보, 전화번호, 법령, 수입/수출 절차, 일반 안내, 기타 FAQ

# 예시
- "관세 예측해줘" → tariff_prediction
- "관세 계산해줘" → tariff_prediction
- "이 물건의 세금이 얼마나 나올까?" → tariff_prediction
- "노트북 샀어" → tariff_prediction
- "미국에서 뭐 샀어" → tariff_prediction
- "운송장 번호 123456 어디쯤이야?" → customs_tracking
- "배송이 어디까지 왔어?" → customs_tracking
- "통관 진행 상황 알려줘" → customs_tracking
- "관세청 전화번호 알려줘" → qna
- "수입 절차가 궁금해" → qna
- "관세청 홈페이지 알려줘" → qna
- "관세법 제12조가 뭐야?" → qna

사용자 쿼리: {query}

반드시 다음 중 하나만 응답하세요: customs_tracking, tariff_prediction, qna
"""

# 의도 분류 결과
INTENT_TYPES = ["customs_tracking", "tariff_prediction", "qna"]

# 기본 의도 (오류 시 사용)
DEFAULT_INTENT = "tariff_prediction"

# 세션 연속성 확인을 위한 메시지 수
SESSION_CHECK_MESSAGE_COUNT = 3

