from typing import Dict, Any, List
import re

from core.shared.states.states import CustomsAgentState
from core.tariff_prediction.tools.calculate_tariff_amount import calculate_tariff_amount
from core.tariff_prediction.tools.get_hs_classification import get_hs_classification
from core.tariff_prediction.tools.clean_product_description import clean_product_description
from core.tariff_prediction.tools.detect_scenario import detect_scenario_from_input
from core.tariff_prediction.tools.parse_user_input import parse_user_input
from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result, generate_hs10_candidates
from core.tariff_prediction.tools.parse_tariff_result import parse_tariff_result
from core.tariff_prediction.constants import (
    SUPPORTED_COUNTRIES, SCENARIOS, OFF_TOPIC_KEYWORDS, CORRECTION_KEYWORDS, 
    SESSION_TERMINATION_KEYWORDS, REPREDICTION_KEYWORDS, SIMPLE_TARIFF_REQUESTS, 
    TARIFF_CONTEXT_KEYWORDS, DEFAULT_EXCHANGE_RATES,
    DEFAULT_COUNTRY, DEFAULT_QUANTITY, DEFAULT_SHIPPING_COST, DEFAULT_SESSION_ID,
    INPUT_EXAMPLES, GUIDE_MESSAGES, ERROR_MESSAGES, CORRECTION_MESSAGES, LLM_PROMPTS
)
from core.tariff_prediction.tools.context_utils import extract_llm_response, extract_info_from_context, merge_context_with_current
from core.tariff_prediction.agent.step_api import tariff_prediction_step_api
from core.tariff_prediction.dto.tariff_request import TariffPredictionRequest
from core.tariff_prediction.dto.tariff_response import TariffPredictionResponse

# 전역 워크플로우 매니저
class WorkflowManager:
    def __init__(self):
        self.sessions = {}
    
    def get_session(self, session_id: str) -> 'TariffPredictionWorkflow':
        """세션을 가져오거나 새로 생성합니다."""
        if session_id not in self.sessions:
            self.sessions[session_id] = TariffPredictionWorkflow()
        return self.sessions[session_id]
    
    def cleanup_session(self, session_id: str):
        """세션을 정리합니다."""
        if session_id in self.sessions:
            del self.sessions[session_id]

# 전역 매니저 인스턴스
workflow_manager = WorkflowManager()

class TariffPredictionWorkflow:
    def __init__(self):
        self.state = {
            'scenario': None,
            'product_name': None,
            'country': None,
            'price': None,
            'quantity': DEFAULT_QUANTITY,
            'shipping_cost': DEFAULT_SHIPPING_COST,
            'hs6_code': None,
            'hs10_code': None,
            'current_step': 'scenario_selection',
            'session_active': False,
            'responses': []
        }
        
        # 환율 지원 국가 목록
        self.supported_countries = SUPPORTED_COUNTRIES
        
        self.scenarios = SCENARIOS

    def reset_session(self):
        """세션을 초기화합니다."""
        self.state = {
            'scenario': None,
            'product_name': None,
            'country': None,
            'price': None,
            'quantity': DEFAULT_QUANTITY,
            'shipping_cost': DEFAULT_SHIPPING_COST,
            'hs6_code': None,
            'hs10_code': None,
            'current_step': 'scenario_selection',
            'session_active': False,
            'responses': []
        }

    def is_supported_country(self, country: str) -> bool:
        """지원되는 국가인지 확인합니다."""
        return country in self.supported_countries

    def get_currency_for_country(self, country: str) -> str:
        """국가에 해당하는 통화를 반환합니다."""
        return self.supported_countries.get(country, 'USD')

    def detect_scenario_from_input(self, user_input: str) -> str | None:
        """사용자 입력에서 시나리오를 자동 감지합니다."""
        return detect_scenario_from_input(user_input)

    def parse_user_input(self, user_input: str) -> Dict[str, Any]:
        """자연어 입력을 파싱합니다."""
        return parse_user_input(user_input)

    def handle_correction_request(self, user_input: str) -> str:
        """수정 요청을 처리합니다."""
        if any(word in user_input for word in CORRECTION_KEYWORDS):
            if self.state['current_step'] == 'scenario_selection':
                return CORRECTION_MESSAGES['scenario_selection']
            elif self.state['current_step'] == 'input_collection':
                return CORRECTION_MESSAGES['input_collection']
            elif self.state['current_step'] == 'hs6_selection':
                # HS6 코드 선택 단계에서 수정 요청 시 바로 재예측 수행
                return self._perform_hs6_reprediction(user_input)
            elif self.state['current_step'] == 'hs10_selection':
                # HS10 코드 선택 단계에서는 재예측 기능 없음
                return "💡 **번호를 입력해 주세요.** (예: 1, 2, 3)"
        
        return ""

    def is_off_topic(self, user_input: str) -> bool:
        """관세 계산과 관련 없는 주제인지 확인합니다."""
        input_lower = user_input.lower()
        return any(keyword in input_lower for keyword in OFF_TOPIC_KEYWORDS)

    def process_user_input(self, user_input: str) -> str:
        """
        사용자 입력을 처리하고 적절한 응답을 반환합니다.
        """
        # 컨텍스트에서 실제 현재 질문 추출
        current_query = user_input
        if "이전 대화:" in user_input and "현재 질문:" in user_input:
            # 컨텍스트가 포함된 경우 현재 질문만 추출
            parts = user_input.split("현재 질문:")
            if len(parts) > 1:
                current_query = parts[1].strip()
        
        # 세션 중단 요청 확인
        if any(word in current_query for word in SESSION_TERMINATION_KEYWORDS):
            self.reset_session()
            return ERROR_MESSAGES['session_terminated']

        # 탈선 처리 - 컨텍스트를 고려하여 더 정확한 판단
        if self.state['session_active']:
            # 이전 대화에서 관세 관련 키워드가 있었는지 확인
            has_tariff_context = any(keyword in user_input.lower() for keyword in TARIFF_CONTEXT_KEYWORDS)
            
            # 관세 관련 컨텍스트가 있으면 탈선으로 간주하지 않음
            if not has_tariff_context and self.is_off_topic(current_query):
                return "현재 관세 계산을 진행 중입니다. 계속 진행하시겠습니까, 아니면 중단하시겠습니까?\n\n계속하려면 '계속'을, 중단하려면 '중단'을 입력해 주세요."

        # 수정 요청 확인
        correction_response = self.handle_correction_request(current_query)
        if correction_response:
            return correction_response

        # 재예측 요청 확인 (HS6 선택 단계에서만)
        if self.state['current_step'] == 'hs6_selection':
            user_input_lower = current_query.lower()
            
            if any(keyword in user_input_lower for keyword in REPREDICTION_KEYWORDS):
                return self._perform_hs6_reprediction(current_query)

        # 간단한 관세 요청인지 확인 ("관세 계산해줘", "관세 예측해줘" 등)
        if current_query.strip() in SIMPLE_TARIFF_REQUESTS:
            return "관세 계산을 위해 다음 정보가 필요합니다:\n\n• 상품명 또는 상품 설명\n• 구매 국가\n• 상품 가격\n• 수량 (선택사항)\n\n💡 **다음과 같이 입력해 주세요:**\n• \"미국에서 150만원에 노트북을 샀어요\"\n• \"일본에서 10만원짜리 이어폰을 구매했어요\"\n• \"독일에서 80만원에 운동화 2켤레를 샀어요\"\n\n위 예시 중 하나를 참고하여 상품 정보를 입력해 주세요."

        # 현재 단계별 처리
        if self.state['current_step'] == 'scenario_selection':
            return self.handle_scenario_selection(current_query)
        elif self.state['current_step'] == 'input_collection':
            return self.handle_input_collection(current_query)
        elif self.state['current_step'] == 'hs6_selection':
            return self.handle_hs6_selection(current_query)
        elif self.state['current_step'] == 'hs10_selection':
            return self.handle_hs10_selection(current_query)

        return "죄송합니다. 현재 상태를 인식할 수 없습니다. 처음부터 다시 시작하겠습니다."

    def handle_scenario_selection(self, user_input: str) -> str:
        """시나리오 선택을 처리합니다."""
        # 자동 감지 시도
        detected_scenario = self.detect_scenario_from_input(user_input)
        if detected_scenario:
            self.state['scenario'] = detected_scenario
            self.state['current_step'] = 'input_collection'
            self.state['session_active'] = True
            response = (
                "구매하신 상품 정보를 입력해 주세요!\n\n"
                "💡 **상품 묘사의 정확도가 높을수록 정확한 관세 예측이 가능합니다!**\n\n"
                "예시:\n"
                "• \"아랫창은 고무로 되어있고 하얀색 운동화를 80000원에 독일에서 샀어요\"\n"
                "• \"인텔 i7 노트북을 150만원에 미국에서 구매했어요\"\n"
                "• \"블루투스 이어폰 2개를 12만원에 일본에서 샀어요\"\n\n"
                "위 예시를 참고하여 상품 정보를 입력해 주세요."
            )
            self.state['responses'].append(response)
            return response
        
        # 수동 선택
        if user_input in self.scenarios:
            self.state['scenario'] = self.scenarios[user_input]
            self.state['current_step'] = 'input_collection'
            self.state['session_active'] = True
            response = (
                "구매하신 상품 정보를 입력해 주세요!\n\n"
                "💡 **상품 묘사의 정확도가 높을수록 정확한 관세 예측이 가능합니다!**\n\n"
                "예시:\n"
                "• \"아랫창은 고무로 되어있고 하얀색 운동화를 80000원에 독일에서 샀어요\"\n"
                "• \"인텔 i7 노트북을 150만원에 미국에서 구매했어요\"\n"
                "• \"블루투스 이어폰 2개를 12만원에 일본에서 샀어요\"\n\n"
                "위 예시를 참고하여 상품 정보를 입력해 주세요."
            )
            self.state['responses'].append(response)
            return response
        
        response = """어떤 시나리오인지 선택해 주세요:

1. 해외직구 (온라인 쇼핑)
2. 해외체류 중 구매 (여행 중 구매)
3. 해외배송 (택배/운송)

💡 **번호를 입력하거나 상황을 설명해 주세요.**\n예시: \"1번\", \"해외직구\", \"여행 중에 샀어요\" 등"""
        self.state['responses'].append(response)
        return response

    def handle_input_collection(self, user_input: str) -> str:
        # 컨텍스트에서 추가 정보 추출 시도
        enhanced_input = user_input
        
        # 이전 대화에서 상품 정보가 누락된 경우 컨텍스트에서 찾기
        if "이전 대화:" in user_input:
            context_part = user_input.split("현재 질문:")[0].replace("이전 대화:", "").strip()
            current_part = user_input.split("현재 질문:")[1].strip() if "현재 질문:" in user_input else user_input
            
            # 컨텍스트에서 상품 정보 추출 시도
            context_info = extract_info_from_context(context_part)
            if context_info:
                # 현재 입력에 누락된 정보를 컨텍스트에서 보완
                enhanced_input = merge_context_with_current(context_info, current_part)
        
        parsed = self.parse_user_input(enhanced_input)
        # 필수 정보 확인
        missing_info = []
        if 'product_name' not in parsed or not parsed['product_name']:
            missing_info.append("상품명")
        if 'country' not in parsed or not parsed['country']:
            missing_info.append("구매 국가")
        if 'price' not in parsed or not parsed['price']:
            missing_info.append("상품 가격")
        if missing_info:
            # 이미 입력된 정보는 보여주고, 누락된 정보만 안내
            info_lines = []
            if 'product_name' in parsed and parsed['product_name']:
                info_lines.append(f"상품명: {parsed['product_name']}")
            if 'country' in parsed and parsed['country']:
                info_lines.append(f"구매 국가: {parsed['country']}")
            if 'price' in parsed and parsed['price']:
                info_lines.append(f"상품 가격: {parsed['price']:,}원")
            if 'quantity' in parsed and parsed['quantity']:
                info_lines.append(f"수량: {parsed['quantity']}개")
            info_str = "\n".join(info_lines)
            missing_str = ", ".join(missing_info)
            response = (
                (info_str + "\n\n" if info_str else "") +
                f"다음 정보가 누락되었습니다: {missing_str}\n"
                "💡 **상품명, 구매 국가, 상품 가격을 모두 입력해 주세요!**\n\n"
                "예시:\n"
                "• \"미국에서 150만원에 노트북을 샀어요\"\n"
                "• \"일본에서 10만원짜리 이어폰을 구매했어요\"\n"
                "• \"독일에서 80만원에 운동화 2켤레를 샀어요\"\n\n"
                "위 예시를 참고하여 상품 정보를 입력해 주세요."
            )
            self.state['responses'].append(response)
            return response
        # 환율 변환 처리
        price = parsed['price']
        price_unit = parsed.get('price_unit', '원')
        
        # 원화가 아닌 경우 환율 변환
        if price_unit != '원':
            try:
                from core.tariff_prediction.tools.get_exchange_rate_info import get_exchange_rate_api
                exchange_rate = get_exchange_rate_api(price_unit, self.state.get('scenario', '해외직구'))
                if exchange_rate:
                    price = price * exchange_rate
                    price_unit = '원'
                else:
                    # 환율 조회 실패 시 기본 환율 사용
                    if price_unit in DEFAULT_EXCHANGE_RATES:
                        price = price * DEFAULT_EXCHANGE_RATES[price_unit]
                        price_unit = '원'
            except Exception as e:
                print(f"[DEBUG] 환율 변환 오류: {e}")
                # 오류 시 기본 환율 사용
                if price_unit in DEFAULT_EXCHANGE_RATES:
                    price = price * DEFAULT_EXCHANGE_RATES[price_unit]
                    price_unit = '원'
        
        # 상태 업데이트
        self.state.update(parsed)
        self.state['price'] = price
        self.state['price_unit'] = price_unit
        
        # step_api.py 활용
        req = TariffPredictionRequest(
            step="input",
            product_description=parsed['product_name'],
            origin_country=parsed['country'],
            price=price,
            quantity=parsed.get('quantity', 1),
            shipping_cost=parsed.get('shipping_cost', 0),
            scenario=self.state.get('scenario')
        )
        resp: TariffPredictionResponse = tariff_prediction_step_api(req)
        if resp.message and (not resp.hs6_candidates):
            self.state['responses'].append(resp.message)
            return resp.message
        self.state['hs6_candidates'] = resp.hs6_candidates
        self.state['current_step'] = 'hs6_selection'
        scenario_str = self.state.get('scenario', '')
        scenario_guide = f"{scenario_str}로 예상하고 안내를 도와드릴게요.\n\n" if scenario_str else ""
        
        # 가격 표시 (원화 변환된 경우)
        price_display = f"{price:,.0f}원"
        if price_unit != '원' and parsed.get('price_unit') != '원':
            original_price = parsed.get('price', price)
            original_unit = parsed.get('price_unit', price_unit)
            price_display = f"{original_price} {original_unit} (약 {price:,.0f}원)"
        
        response = scenario_guide + f"상품묘사: {parsed['product_name']}\n국가: {parsed['country']}\n가격: {price_display}\n수량: {parsed.get('quantity', 1)}개\n\nHS 코드 예측 모델로부터 HS6 코드 후보를 찾았습니다. 번호를 선택해 주세요:\n" + '\n'.join([
                            f"{i+1}. {c['description']} (신뢰도: {c['confidence']:.1%})" for i, c in enumerate(resp.hs6_candidates or [])
        ]) + f"\n\n💡 **위 후보 중 하나를 선택해 주세요.**\n예시: \"1번\", \"2번\", \"3번\" 등"
        self.state['responses'].append(response)
        return response

    def parse_hs6_result(self, hs6_result: str) -> List[Dict]:
        """HS6 결과를 파싱합니다."""
        return parse_hs6_result(hs6_result)

    def format_hs6_candidates(self) -> str:
        """HS6 후보를 포맷팅합니다."""
        formatted = ""
        for i, candidate in enumerate(self.state['hs6_candidates'], 1):
            formatted += f"{i}. {candidate['code']} - {candidate['description']} (신뢰도: {candidate['confidence']:.1%})\n"
        return formatted

    def handle_hs6_selection(self, user_input: str) -> str:
        from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result
        from core.shared.utils.llm import get_llm
        
        # 숫자 입력 확인
        number_match = re.search(r'(\d+)', user_input)
        
        if number_match and self.state.get('hs6_candidates'):
            # 번호가 입력된 경우 - 기존 로직
            selection = int(number_match.group(1))
            candidates = self.state['hs6_candidates']
            if 1 <= selection <= len(candidates):
                selected = candidates[selection - 1]
                self.state['hs6_code'] = selected['code']
                # step_api.py 활용
                req = TariffPredictionRequest(
                    step="hs6_select",
                    hs6_code=selected['code']
                )
                resp: TariffPredictionResponse = tariff_prediction_step_api(req)
                if resp.message and (not resp.hs10_candidates):
                    self.state['responses'].append(resp.message)
                    return resp.message
                self.state['hs10_candidates'] = resp.hs10_candidates
                self.state['current_step'] = 'hs10_selection'
                response = f"선택하신 HS 6자리 코드: {selected['code']}\n\nHS 10자리 코드 후보를 선택해 주세요:\n" + '\n'.join([
                    f"{i+1}. {c['code']} - {c['description']}" for i, c in enumerate(resp.hs10_candidates or [])
                ]) + f"\n\n💡 **위 후보 중 하나를 선택해 주세요.**\n예시: \"1번\", \"2번\", \"3번\" 등"
                self.state['responses'].append(response)
                return response
            else:
                response = f"**잘못된 번호입니다.**\n\n1부터 {len(candidates)} 사이의 번호를 다시 입력해 주세요.\n\n예시: \"1번\", \"2번\", \"3번\" 등"
                self.state['responses'].append(response)
                return response
        else:
            # 번호가 아닌 입력인 경우 - 재예측 의도 판단
            try:
                # 간단한 키워드 기반 판단으로 먼저 시도
                reprediction_keywords = ["없다", "코드가 없다", "재예측", "다시", "틀렸다", "맞지 않다", "다른", "새로", "다시 예측", "다른 코드", "적합하지 않다", "코드가 없어"]
                user_input_lower = user_input.lower()
                
                # 키워드 매칭으로 빠른 판단
                if any(keyword in user_input_lower for keyword in reprediction_keywords):
                    return self._perform_hs6_reprediction(user_input)
                
                # 키워드 매칭이 안 되면 LLM으로 판단
                llm = get_llm()
                
                # 재예측 의도 판단을 위한 명확한 프롬프트
                intent_prompt = f"""사용자의 입력이 HS 코드 후보가 적합하지 않아서 재예측을 요청하는 의도인지 판단해주세요.

재예측 의도로 보이는 키워드: "없다", "코드가 없다", "재예측", "다시", "틀렸다", "맞지 않다", "다른", "새로", "다시 예측", "다른 코드", "적합하지 않다"

사용자 입력: {user_input}

위 입력이 재예측을 요청하는 의도인지 판단하여 '네' 또는 '아니오'로만 답변하세요. 반드시 한 단어로만 답변하세요."""

                response = llm.invoke([{"role": "user", "content": intent_prompt}])
                
                # LLM 응답을 안전하게 추출
                answer = self._extract_llm_response(response)
                
                if answer.lower() in ["네", "yes", "true", "1"]:
                    # 재예측 의도로 판단된 경우
                    return self._perform_hs6_reprediction(user_input)
                else:
                    # 재예측 의도가 아닌 경우 안내 메시지
                    response = f"💡 **번호를 입력해 주세요.** (예: 1, 2, 3)\n\n만약 후보가 모두 적합하지 않으면 '코드가 없다', '다시', '재예측' 등으로 입력해 주세요."
                    self.state['responses'].append(response)
                    return response
                    
            except Exception as e:
                print(f"[DEBUG] handle_hs6_selection intent detection error: {e}")
                # 예외 발생 시 안내 메시지로 graceful 처리
                response = f"입력 처리 중 오류가 발생했습니다. 숫자를 입력하거나, 재예측을 원하시면 '다시', '재예측' 등으로 입력해 주세요."
                self.state['responses'].append(response)
                return response

    def generate_hs10_candidates(self, hs6_code: str) -> List[Dict]:
        """HS10 후보를 생성합니다."""
        return generate_hs10_candidates(hs6_code)

    def format_hs10_candidates(self) -> str:
        """HS10 후보를 포맷팅합니다."""
        formatted = ""
        for i, candidate in enumerate(self.state['hs10_candidates'], 1):
            formatted += f"{i}. {candidate['code']} - {candidate['description']}\n"
        return formatted

    def handle_hs10_selection(self, user_input: str) -> str:
        # 숫자 입력 확인
        number_match = re.search(r'(\d+)', user_input)
        
        if number_match and self.state.get('hs10_candidates'):
            # 번호가 입력된 경우 - 기존 로직
            selection = int(number_match.group(1))
            candidates = self.state['hs10_candidates']
            if 1 <= selection <= len(candidates):
                selected = candidates[selection - 1]
                self.state['hs10_code'] = selected['code']
                # step_api.py 활용
                country = self.state.get('country', DEFAULT_COUNTRY)  # 기본값으로 미국 설정
                if not country or country.strip() == "":
                    country = DEFAULT_COUNTRY  # 빈 문자열이면 기본값 사용
                
                req = TariffPredictionRequest(
                    step="hs10_select",
                    hs10_code=selected['code'],
                    origin_country=country,
                    price=self.state.get('price'),
                    quantity=self.state.get('quantity', 1),
                    shipping_cost=self.state.get('shipping_cost', 0),
                    scenario=self.state.get('scenario')
                )
                resp: TariffPredictionResponse = tariff_prediction_step_api(req)
                self.reset_session()
                if resp.calculation_result:
                    response = f"# 🎯 관세 계산 결과\n{resp.calculation_result}\n\n{resp.message or ''}"
                    self.state['responses'].append(response)
                    return response
                else:
                    response = resp.message or "계산 결과를 가져오지 못했습니다."
                    self.state['responses'].append(response)
                    return response
            else:
                response = f"**잘못된 번호입니다.**\n\n1부터 {len(candidates)} 사이의 번호를 다시 입력해 주세요.\n\n예시: \"1번\", \"2번\", \"3번\" 등"
                self.state['responses'].append(response)
                return response
        else:
            # 번호가 아닌 입력인 경우 - 단순히 번호 입력 안내
            response = f"💡 **번호를 입력해 주세요.** (예: 1, 2, 3)"
            self.state['responses'].append(response)
            return response



    def _perform_hs6_reprediction(self, user_input: str) -> str:
        """HS6 코드 재예측을 수행합니다."""
        from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result
        from core.shared.utils.llm import get_llm
        
        product_name = self.state.get('product_name')
        if not product_name or not isinstance(product_name, str) or not product_name.strip():
            response = "상품명을 알 수 없어 HS 코드 예측을 다시 시도할 수 없습니다. 처음부터 다시 입력해 주세요."
            self.state['responses'].append(response)
            return response
        
        try:
            # 재예측을 위한 명확한 프롬프트
            reprediction_prompt = f"""아래 상품명과 사용자의 추가 의견을 참고하여 HS 코드 후보를 예측해주세요.

상품명: {product_name}
사용자 추가 의견: {user_input}

다음 형식으로 HS 코드 후보 3개 이내를 반환하세요:
1. [6자리 HS코드] (확률: [확률]%)
2. [6자리 HS코드] (확률: [확률]%)
3. [6자리 HS코드] (확률: [확률]%)

예시:
1. 851770 (확률: 85.5%)
2. 851712 (확률: 12.3%)
3. 851713 (확률: 2.2%)"""

            llm = get_llm()
            hs6_response = llm.invoke([{"role": "user", "content": reprediction_prompt}])
            hs6_result = extract_llm_response(hs6_response)
            
            # LLM 응답이 비어있거나 잘못된 경우 처리
            if not hs6_result or len(hs6_result.strip()) < 10:
                response = "HS 코드 예측에 실패했습니다. 상품명을 더 구체적으로 입력해 주세요."
                self.state['responses'].append(response)
                return response
            
            # parse_hs6_result 함수 호출 시 예외 처리
            try:
                hs6_candidates = parse_hs6_result(hs6_result)
            except Exception as parse_error:
                print(f"[DEBUG] parse_hs6_result error: {parse_error}")
                response = "HS 코드 예측 결과를 처리하는 중 오류가 발생했습니다. 다시 시도해 주세요."
                self.state['responses'].append(response)
                return response
            
            if not hs6_candidates:
                response = "HS 코드 예측에 다시 실패했습니다. 상품명을 더 구체적으로 입력해 주세요."
                self.state['responses'].append(response)
                return response
            
            self.state['hs6_candidates'] = hs6_candidates
            scenario_str = self.state.get('scenario', '')
            scenario_guide = f"{scenario_str}로 예상하고 안내를 도와드릴게요.\n\n" if scenario_str else ""
            
            response = scenario_guide + f"상품묘사: {product_name}\n국가: {self.state.get('country','')}\n가격: {self.state.get('price',0):,}원\n수량: {self.state.get('quantity',1)}개\n\nHS 코드 재예측 결과입니다. 번호를 선택해 주세요:\n" + '\n'.join([
                f"{i+1}. {c['description']} (신뢰도: {c['confidence']:.1%})" for i, c in enumerate(hs6_candidates)
            ]) + f"\n\n💡 **위 후보 중 하나를 선택해 주세요.**\n예시: \"1번\", \"2번\", \"3번\" 등"
            
            self.state['responses'].append(response)
            return response
            
        except Exception as e:
            print(f"[DEBUG] _perform_hs6_reprediction error: {e}")
            response = "HS 코드 재예측 중 오류가 발생했습니다. 다시 시도해 주세요."
            self.state['responses'].append(response)
            return response

    def _perform_hs10_reprediction(self, user_input: str) -> str:
        """HS10 코드 재예측을 수행합니다."""
        from core.tariff_prediction.tools.parse_hs_results import generate_hs10_candidates
        from core.shared.utils.llm import get_llm
        
        hs6_code = self.state.get('hs6_code')
        if not hs6_code:
            response = "HS6 코드가 없어 HS10 코드 예측을 다시 시도할 수 없습니다. HS6 코드부터 다시 선택해 주세요."
            self.state['responses'].append(response)
            return response
        
        try:
            # HS6 코드를 기반으로 HS10 후보 생성
            hs10_candidates = generate_hs10_candidates(hs6_code)
            
            if not hs10_candidates:
                response = "HS10 코드 예측에 실패했습니다. HS6 코드를 다시 선택해 주세요."
                self.state['responses'].append(response)
                return response
            
            self.state['hs10_candidates'] = hs10_candidates
            
            response = f"HS 6자리 코드: {hs6_code}\n\nHS 10자리 코드 재예측 결과입니다. 번호를 선택해 주세요:\n" + '\n'.join([
                f"{i+1}. {c['code']} - {c['description']}" for i, c in enumerate(hs10_candidates)
            ]) + f"\n\n💡 **위 후보 중 하나를 선택해 주세요.**\n예시: \"1번\", \"2번\", \"3번\" 등"
            
            self.state['responses'].append(response)
            return response
            
        except Exception as e:
            print(f"[DEBUG] _perform_hs10_reprediction error: {e}")
            response = "HS10 코드 재예측 중 오류가 발생했습니다. 다시 시도해 주세요."
            self.state['responses'].append(response)
            return response

    def perform_calculation(self) -> str:
        """최종 계산을 수행합니다."""
        try:
            # 관세 계산
            tariff_result = calculate_tariff_amount(
                product_code=self.state['hs10_code'],
                value=self.state['price'],
                origin_country=self.state['country'],
                item_count=self.state['quantity'],
                shipping_cost=self.state['shipping_cost'],
                situation=self.state['scenario']
            )
            
            # f-string을 이용한 친화적인 결과 문장 생성
            friendly_result = self.generate_friendly_result(tariff_result)
            
            # 세션 종료
            self.reset_session()
            
            return friendly_result
            
        except Exception as e:
            self.reset_session()
            return f"계산 중 오류가 발생했습니다: {str(e)}"

    def generate_friendly_result(self, tariff_result: str) -> str:
        """친화적인 결과 문장을 생성합니다."""
        # 관세 계산 결과 파싱
        parsed_result = self.parse_tariff_result(tariff_result)
        
        product_name = self.state.get('product_name', '상품')
        country = self.state.get('country', '해당 국가')
        price = self.state.get('price', 0)
        scenario = self.state.get('scenario', '해외직구')
        
        # 마크다운 형식의 친화적인 메시지
        friendly_message = f"""# 🎯 관세 계산 완료!

## 📦 상품 정보
- **상품묘사**: {product_name}
- **구매 국가**: {country}
- **상품 가격**: {price:,}원
- **시나리오**: {scenario}

## 📊 계산 결과
{parsed_result['formatted_result']}

## 💡 참고사항
- 위 금액은 예상 관세이며, 실제 관세는 세관 심사 결과에 따라 달라질 수 있습니다.
- 정확한 관세는 통관 시 세관에서 최종 결정됩니다.
- 추가 문의사항이 있으시면 언제든 말씀해 주세요!
        """
        
        return friendly_message

    def parse_tariff_result(self, tariff_result: str) -> Dict[str, Any]:
        """관세 계산 결과를 파싱합니다."""
        return parse_tariff_result(tariff_result)
    


def tariff_prediction_agent(state: CustomsAgentState) -> CustomsAgentState:
    """개선된 관세 예측 에이전트"""
    
    print(f"[DEBUG] tariff_prediction_agent called with query: {state['query']}")
    
    # 세션 ID 생성 (실제로는 사용자 ID나 세션 ID를 사용)
    session_id = DEFAULT_SESSION_ID  # 실제 구현에서는 고유한 세션 ID 사용
    
    # 워크플로우 세션 가져오기
    workflow = workflow_manager.get_session(session_id)
    
    # 대화 히스토리에서 이전 컨텍스트 추출
    messages = state.get("messages", [])
    context = ""
    previous_llm_responses = []
    
    if messages:
        # 최근 5개의 메시지에서 사용자 입력과 AI 응답 추출
        recent_messages = messages[-10:]  # 최근 10개 메시지 확인
        
        user_messages = []
        for msg in recent_messages:
            if hasattr(msg, 'type'):
                if msg.type == 'human':
                    user_messages.append(msg.content)
                elif msg.type == 'ai':
                    # AI 응답에서 HS 코드 후보 정보 추출
                    if hasattr(msg, 'content') and isinstance(msg.content, str):
                        content = msg.content
                        if any(keyword in content for keyword in ['HS6 코드 후보', 'HS10 코드 후보', '번호를 선택']):
                            previous_llm_responses.append(content)
        
        if user_messages:
            context = " ".join(user_messages[-5:])  # 최근 5개 사용자 메시지
    
    # 이전 LLM 응답 정보를 포함한 컨텍스트 구성
    enhanced_context = context or ""
    if previous_llm_responses:
        enhanced_context += f"\n\n이전 LLM 응답:\n" + "\n".join(previous_llm_responses[-2:])  # 최근 2개 LLM 응답
    
    # 컨텍스트가 있으면 쿼리와 결합
    if enhanced_context:
        enhanced_query = f"이전 대화 및 LLM 응답: {enhanced_context}\n\n현재 질문: {state['query']}"
        print(f"[DEBUG] Enhanced query with LLM context: {enhanced_query}")
        response = workflow.process_user_input(enhanced_query)
    else:
        response = workflow.process_user_input(state["query"])
    
    print(f"[DEBUG] tariff_prediction_agent response: {response}")
    
    state["final_response"] = response
    return state