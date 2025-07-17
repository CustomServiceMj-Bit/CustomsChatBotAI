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
from core.tariff_prediction.constants import SUPPORTED_COUNTRIES, SCENARIOS, OFF_TOPIC_KEYWORDS, CORRECTION_KEYWORDS, SESSION_TERMINATION_KEYWORDS
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
            'quantity': 1,
            'shipping_cost': 0,
            'hs6_code': None,
            'hs10_code': None,
            'current_step': 'scenario_selection',
            'session_active': False
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
            'quantity': 1,
            'shipping_cost': 0,
            'hs6_code': None,
            'hs10_code': None,
            'current_step': 'scenario_selection',
            'session_active': False
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
                return "어떤 정보를 수정하시겠습니까?\n1. 시나리오\n2. 상품 정보\n3. 처음부터 다시 시작"
            elif self.state['current_step'] == 'input_collection':
                return "어떤 정보를 수정하시겠습니까?\n1. 상품묘사\n2. 국가\n3. 가격\n4. 수량\n5. 배송비\n6. 처음부터 다시 시작"
            elif self.state['current_step'] == 'hs6_selection':
                return "HS6 코드 선택을 다시 하시겠습니까?"
            elif self.state['current_step'] == 'hs10_selection':
                return "HS10 코드 선택을 다시 하시겠습니까?"
        
        return None

    def is_off_topic(self, user_input: str) -> bool:
        """관세 계산과 관련 없는 주제인지 확인합니다."""
        input_lower = user_input.lower()
        return any(keyword in input_lower for keyword in OFF_TOPIC_KEYWORDS)

    def process_user_input(self, user_input: str) -> str:
        """
        사용자 입력을 처리하고 적절한 응답을 반환합니다.
        """
        # 세션 중단 요청 확인
        if any(word in user_input for word in SESSION_TERMINATION_KEYWORDS):
            self.reset_session()
            return "관세 계산을 중단하겠습니다. 다른 질문이 있으시면 언제든 말씀해 주세요."

        # 탈선 처리
        if self.state['session_active'] and self.is_off_topic(user_input):
            return "현재 관세 계산을 진행 중입니다. 계속 진행하시겠습니까, 아니면 중단하시겠습니까?\n\n계속하려면 '계속'을, 중단하려면 '중단'을 입력해 주세요."

        # 수정 요청 확인
        correction_response = self.handle_correction_request(user_input)
        if correction_response:
            return correction_response

        # 현재 단계별 처리
        if self.state['current_step'] == 'scenario_selection':
            return self.handle_scenario_selection(user_input)
        elif self.state['current_step'] == 'input_collection':
            return self.handle_input_collection(user_input)
        elif self.state['current_step'] == 'hs6_selection':
            return self.handle_hs6_selection(user_input)
        elif self.state['current_step'] == 'hs10_selection':
            return self.handle_hs10_selection(user_input)
        # elif self.state['current_step'] == 'calculation':
        #     return self.handle_calculation(user_input)

        return "죄송합니다. 현재 상태를 인식할 수 없습니다. 처음부터 다시 시작하겠습니다."

    def handle_scenario_selection(self, user_input: str) -> str:
        """시나리오 선택을 처리합니다."""
        # 자동 감지 시도
        detected_scenario = self.detect_scenario_from_input(user_input)
        if detected_scenario:
            self.state['scenario'] = detected_scenario
            self.state['current_step'] = 'input_collection'
            self.state['session_active'] = True
            return f"'{detected_scenario}'로 인식했습니다! 이제 구매하신 상품에 대해 자유롭게 말씀해 주세요.\n\n💡 **상품 묘사의 정확도가 높을수록 정확한 관세 예측이 가능합니다!**\n\n예시:\n• \"아랫창은 고무로 되어있고 하얀색 운동화를 80000원에 독일에서 샀어요\"\n• \"인텔 i7 노트북을 150만원에 미국에서 구매했어요\"\n• \"블루투스 이어폰 2개를 12만원에 일본에서 샀어요\""
        
        # 수동 선택
        if user_input in self.scenarios:
            self.state['scenario'] = self.scenarios[user_input]
            self.state['current_step'] = 'input_collection'
            self.state['session_active'] = True
            return f"'{self.state['scenario']}'로 선택하셨습니다! 이제 구매하신 상품에 대해 자유롭게 말씀해 주세요.\n\n💡 **상품 묘사의 정확도가 높을수록 정확한 관세 예측이 가능합니다!**\n\n예시:\n• \"아랫창은 고무로 되어있고 하얀색 운동화를 80000원에 독일에서 샀어요\"\n• \"인텔 i7 노트북을 150만원에 미국에서 구매했어요\"\n• \"블루투스 이어폰 2개를 12만원에 일본에서 샀어요\""
        
        return """어떤 시나리오인지 선택해 주세요:

1. 해외직구 (온라인 쇼핑)
2. 해외체류 중 구매 (여행 중 구매)
3. 해외배송 (택배/운송)

번호를 입력하거나 상황을 설명해 주세요."""

    def handle_input_collection(self, user_input: str) -> str:
        parsed = self.parse_user_input(user_input)
        # 필수 정보 확인
        missing_info = []
        if 'product_name' not in parsed:
            missing_info.append("상품에 대한 묘사")
        if 'country' not in parsed:
            missing_info.append("구매 국가")
        if 'price' not in parsed:
            missing_info.append("상품 가격")
        if missing_info:
            missing_str = ", ".join(missing_info)
            return f"다음 정보가 누락되었습니다: {missing_str}\n\n💡 **상품 묘사의 정확도가 높을수록 정확한 관세 예측이 가능합니다!**\n\n예시:\n• \"아랫창은 고무로 되어있고 하얀색 운동화를 80000원에 독일에서 샀어요\"\n• \"인텔 i7 노트북을 150만원에 미국에서 구매했어요\"\n• \"블루투스 이어폰 2개를 12만원에 일본에서 샀어요\""
        # 상태 업데이트
        self.state.update(parsed)
        # step_api.py 활용
        req = TariffPredictionRequest(
            step="input",
            product_description=parsed['product_name'],
            origin_country=parsed['country'],
            price=parsed['price'],
            quantity=parsed.get('quantity', 1),
            shipping_cost=parsed.get('shipping_cost', 0),
            scenario=self.state.get('scenario')
        )
        resp: TariffPredictionResponse = tariff_prediction_step_api(req)
        self.state['hs6_candidates'] = resp.hs6_candidates
        self.state['current_step'] = 'hs6_selection'
        return f"상품묘사: {parsed['product_name']}\n국가: {parsed['country']}\n가격: {parsed['price']:,}원\n수량: {parsed.get('quantity', 1)}개\n\nHS6 코드 후보를 찾았습니다. 번호를 선택해 주세요:\n" + '\n'.join([
            f"{i+1}. {c['code']} - {c['description']} (신뢰도: {c['confidence']})" for i, c in enumerate(resp.hs6_candidates or [])
        ])

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
        number_match = re.search(r'(\d+)', user_input)
        if number_match and self.state.get('hs6_candidates'):
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
                self.state['hs10_candidates'] = resp.hs10_candidates
                self.state['current_step'] = 'hs10_selection'
                return f"선택하신 HS6 코드: {selected['code']}\n\nHS10 코드 후보를 선택해 주세요:\n" + '\n'.join([
                    f"{i+1}. {c['code']} - {c['description']}" for i, c in enumerate(resp.hs10_candidates or [])
                ])
            else:
                return f"1부터 {len(candidates)} 사이의 번호를 입력해 주세요."
        else:
            return f"숫자를 입력해 주세요. (예: 1, 2, 3)"

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
        number_match = re.search(r'(\d+)', user_input)
        if number_match and self.state.get('hs10_candidates'):
            selection = int(number_match.group(1))
            candidates = self.state['hs10_candidates']
            if 1 <= selection <= len(candidates):
                selected = candidates[selection - 1]
                self.state['hs10_code'] = selected['code']
                # step_api.py 활용
                req = TariffPredictionRequest(
                    step="hs10_select",
                    hs10_code=selected['code'],
                    origin_country=self.state.get('country'),
                    price=self.state.get('price'),
                    quantity=self.state.get('quantity', 1),
                    shipping_cost=self.state.get('shipping_cost', 0),
                    scenario=self.state.get('scenario')
                )
                resp: TariffPredictionResponse = tariff_prediction_step_api(req)
                self.reset_session()
                if resp.calculation_result:
                    return f"# 🎯 관세 계산 결과\n{resp.calculation_result}\n\n{resp.message or ''}"
                else:
                    return resp.message or "계산 결과를 가져오지 못했습니다."
            else:
                return f"1부터 {len(candidates)} 사이의 번호를 입력해 주세요."
        else:
            return f"숫자를 입력해 주세요. (예: 1, 2, 3)"

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
    
    # 세션 ID 생성 (실제로는 사용자 ID나 세션 ID를 사용)
    session_id = "default_session"  # 실제 구현에서는 고유한 세션 ID 사용
    
    # 워크플로우 세션 가져오기
    workflow = workflow_manager.get_session(session_id)
    
    # 사용자 입력 처리
    response = workflow.process_user_input(state["query"])
    
    state["final_response"] = response
    return state