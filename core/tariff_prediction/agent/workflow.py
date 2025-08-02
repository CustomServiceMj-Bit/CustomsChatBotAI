from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import re
from core.tariff_prediction.constants import (
    SUPPORTED_COUNTRIES, DEFAULT_QUANTITY, DEFAULT_SHIPPING_COST, OFF_TOPIC_KEYWORDS, CORRECTION_KEYWORDS, SESSION_TERMINATION_KEYWORDS, SIMPLE_TARIFF_REQUESTS, TARIFF_CONTEXT_KEYWORDS, DEFAULT_EXCHANGE_RATES, DEFAULT_COUNTRY, ERROR_MESSAGES, CORRECTION_MESSAGES, RESPONSE_MESSAGES, STATE_KEYS, STEPS, LLM_PROMPTS
)
from core.tariff_prediction.tools.detect_scenario import detect_scenario_from_input
from core.tariff_prediction.tools.parse_user_input import parse_user_input
from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result, generate_hs10_candidates
from core.tariff_prediction.tools.parse_tariff_result import parse_tariff_result
from core.tariff_prediction.tools.context_utils import extract_llm_response, extract_info_from_context, merge_context_with_current
from core.tariff_prediction.agent.step_api import tariff_prediction_step_api
from core.tariff_prediction.dto.tariff_request import TariffPredictionRequest
from core.tariff_prediction.dto.tariff_response import TariffPredictionResponse

@dataclass
class TariffState:
    scenario: Optional[str] = None
    product_name: Optional[str] = None
    country: Optional[str] = None
    price: Optional[float] = None
    quantity: int = DEFAULT_QUANTITY
    shipping_cost: float = DEFAULT_SHIPPING_COST
    hs6_code: Optional[str] = None
    hs10_code: Optional[str] = None
    current_step: str = 'scenario_selection'
    session_active: bool = False
    responses: list = field(default_factory=list)
    predicted_scenario: Optional[str] = None
    last_user_input: Optional[str] = None
    hs6_candidates: Optional[list] = field(default_factory=list)
    hs10_candidates: Optional[list] = field(default_factory=list)
    price_unit: str = '원'

class WorkflowManager:
    def __init__(self):
        self.sessions = {}
    def get_session(self, session_id: str) -> 'TariffPredictionWorkflow':
        if session_id not in self.sessions:
            self.sessions[session_id] = TariffPredictionWorkflow()
        return self.sessions[session_id]
    def cleanup_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

workflow_manager = WorkflowManager()

class TariffPredictionWorkflow:
    def __init__(self):
        self.state = TariffState()
        self.supported_countries = SUPPORTED_COUNTRIES
        self.step_to_handler = {
            'scenario_selection': self.handle_scenario_selection,
            'input_collection': self.handle_input_collection,
            'hs6_selection': self.handle_hs6_selection,
            'hs10_selection': self.handle_hs10_selection,
        }

    def reset_session(self):
        self.state = TariffState()

    def process_user_input(self, user_input: str) -> str:
        handler = self.step_to_handler.get(self.state.current_step, self.handle_unknown_step)
        return handler(user_input)

    def handle_unknown_step(self, user_input: str) -> str:
        return RESPONSE_MESSAGES['unrecognized_state']

    def is_supported_country(self, country: str) -> bool:
        return country in self.supported_countries

    def get_currency_for_country(self, country: str) -> str:
        return self.supported_countries.get(country, 'USD')

    def detect_scenario_from_input(self, user_input: str) -> str | None:
        return detect_scenario_from_input(user_input)

    def parse_user_input(self, user_input: str) -> Dict[str, Any]:
        return parse_user_input(user_input)

    def handle_correction_request(self, user_input: str) -> str:
        if any(word in user_input for word in CORRECTION_KEYWORDS):
            if self.state.current_step == 'scenario_selection':
                return CORRECTION_MESSAGES['scenario_selection']
            elif self.state.current_step == 'input_collection':
                return CORRECTION_MESSAGES['input_collection']
            elif self.state.current_step == 'hs6_selection':
                return self._perform_hs6_reprediction(user_input)
            elif self.state.current_step == 'hs10_selection':
                return RESPONSE_MESSAGES['hs10_reprediction_not_available']
        return ""

    def is_off_topic(self, user_input: str) -> bool:
        input_lower = user_input.lower()
        return any(keyword in input_lower for keyword in OFF_TOPIC_KEYWORDS)

    def handle_scenario_selection(self, user_input: str) -> str:
        detected_scenario = self.detect_scenario_from_input(user_input)
        if detected_scenario:
            self.state.scenario = detected_scenario
            self.state.current_step = 'input_collection'
            self.state.session_active = True
            response = RESPONSE_MESSAGES['input_collection_prompt']
            self.state.responses.append(response)
            return response
        self.state.current_step = 'input_collection'
        self.state.session_active = True
        response = RESPONSE_MESSAGES['input_collection_prompt']
        self.state.responses.append(response)
        return response

    def josa_으로(self, word: str) -> str:
        if not word:
            return ""
        last_char = word[-1]
        if (ord(last_char) - 44032) % 28 == 0:
            return word + "로"
        else:
            return word + "으로"

    def handle_input_collection(self, user_input: str) -> str:
        if not self.state.scenario:
            predicted = self.detect_scenario_from_input(user_input)
            if predicted:
                self.state.scenario = predicted
        enhanced_input = user_input
        if "이전 대화:" in user_input:
            context_part = user_input.split("현재 질문:")[0].replace("이전 대화:", "").strip()
            current_part = user_input.split("현재 질문:")[1].strip() if "현재 질문:" in user_input else user_input
            context_info = extract_info_from_context(context_part)
            if context_info:
                enhanced_input = merge_context_with_current(context_info, current_part)
        parsed = self.parse_user_input(enhanced_input)
        if 'product_name' not in parsed or not parsed['product_name']:
            cleaned_input = user_input.strip()
            for keyword in ['관세', '예측', '계산', '해줘', '알려줘', '어떻게', '해주세요']:
                cleaned_input = cleaned_input.replace(keyword, '').strip()
            if cleaned_input:
                parsed['product_name'] = cleaned_input
        missing_info = []
        if 'product_name' not in parsed or not parsed['product_name']:
            missing_info.append("상품명")
        if 'country' not in parsed or not parsed['country']:
            missing_info.append("구매 국가")
        if 'price' not in parsed or not parsed['price']:
            missing_info.append("상품 가격")
        if missing_info:
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
                f"{RESPONSE_MESSAGES['missing_info_prompt']} {missing_str}\n"
                f"{RESPONSE_MESSAGES['product_info_example']}"
            )
            self.state.responses.append(response)
            return response
        price = parsed['price']
        price_unit = parsed.get('price_unit', '원')
        if price_unit != '원':
            try:
                from core.tariff_prediction.tools.get_exchange_rate_info import get_exchange_rate_api
                exchange_rate = get_exchange_rate_api(price_unit, self.state.scenario)
                if exchange_rate:
                    price = price * exchange_rate
                    price_unit = '원'
                else:
                    if price_unit in DEFAULT_EXCHANGE_RATES:
                        price = price * DEFAULT_EXCHANGE_RATES[price_unit]
                        price_unit = '원'
            except Exception:
                if price_unit in DEFAULT_EXCHANGE_RATES:
                    price = price * DEFAULT_EXCHANGE_RATES[price_unit]
                    price_unit = '원'
        self.state.__dict__.update(parsed)
        self.state.price = price
        self.state.price_unit = price_unit
        req = TariffPredictionRequest(
            step=STEPS['input'],
            product_description=parsed['product_name'],
            origin_country=parsed['country'],
            price=price,
            quantity=parsed.get('quantity', 1),
            shipping_cost=parsed.get('shipping_cost', 0),
            scenario=self.state.scenario
        )
        resp: TariffPredictionResponse = tariff_prediction_step_api(req)
        if resp.message and (not resp.hs6_candidates):
            self.state.responses.append(resp.message)
            return resp.message
        self.state.hs6_candidates = resp.hs6_candidates
        self.state.current_step = STEPS['hs6_selection']
        scenario_str = self.state.scenario
        scenario_guide = f"{self.josa_으로(scenario_str)} {RESPONSE_MESSAGES['scenario_guide_prefix']}\n\n" if scenario_str else ""
        price_display = f"{price:,.0f}원"
        if price_unit != '원' and parsed.get('price_unit') != '원':
            original_price = parsed.get('price', price)
            original_unit = parsed.get('price_unit', price_unit)
            price_display = f"{original_price} {original_unit} ({price:,.0f}원)"
        response = scenario_guide + f"상품묘사: {parsed['product_name']}\n국가: {parsed['country']}\n가격: {price_display}\n수량: {parsed.get('quantity', 1)}개\n\n{RESPONSE_MESSAGES['hs6_code_prediction_prompt']}\n" + '\n'.join([
                            f"{i+1}. {c['description']} ({RESPONSE_MESSAGES['hs6_confidence']} {c['confidence']:.1%})" for i, c in enumerate(resp.hs6_candidates or [])
        ]) + f"\n\n{self.format_selection_guide('hs6_code_selection_prompt')}"
        self.state.responses.append(response)
        return response

    def format_selection_guide(self, selection_prompt_key: str) -> str:
        return (
            f"{RESPONSE_MESSAGES[selection_prompt_key]}\n"
            f"{RESPONSE_MESSAGES['number_example']}\n"
            f"{RESPONSE_MESSAGES['reprediction_guide']}"
        )

    def handle_hs6_selection(self, user_input: str) -> str:
        from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result
        from core.shared.utils.llm import get_llm
        number_match = re.search(r'(\d+)', user_input)
        if number_match and self.state.hs6_candidates:
            selection = int(number_match.group(1))
            candidates = self.state.hs6_candidates
            if 1 <= selection <= len(candidates):
                selected = candidates[selection - 1]
                self.state.hs6_code = selected['code']
                req = TariffPredictionRequest(
                    step=STEPS['hs6_select'],
                    hs6_code=selected['code']
                )
                resp: TariffPredictionResponse = tariff_prediction_step_api(req)
                if resp.message and (not resp.hs10_candidates):
                    self.state.responses.append(resp.message)
                    return resp.message
                self.state.hs10_candidates = resp.hs10_candidates
                self.state.current_step = STEPS['hs10_selection']
                response = f"{RESPONSE_MESSAGES['hs6_code_selected']} {selected['code']}\n\n{RESPONSE_MESSAGES['hs10_code_prediction_prompt']}\n" + '\n'.join([
                    f"{i+1}. {c['code']} - {c['description']}" for i, c in enumerate(resp.hs10_candidates or [])
                ]) + f"\n\n{self.format_selection_guide('hs10_code_selection_prompt')}"
                self.state.responses.append(response)
                return response
            else:
                response = self.format_selection_guide('hs6_code_selection_prompt')
                self.state.responses.append(response)
                return response
        else:
            try:
                llm = get_llm()
                intent_prompt = f"{LLM_PROMPTS['hs6_reprediction_intent']}\n\n{LLM_PROMPTS['hs6_reprediction_keywords']}\n\n{LLM_PROMPTS['user_input']}: {user_input}\n\n{LLM_PROMPTS['hs6_reprediction_prompt_response']}"
                response = llm.invoke([{"role": "user", "content": intent_prompt}])
                answer = extract_llm_response(response)
                if answer.lower() in ["네", "yes", "true", "1"]:
                    return self._perform_hs6_reprediction(user_input)
                else:
                    response = self.format_selection_guide('hs6_code_selection_prompt')
                    self.state.responses.append(response)
                    return response
            except Exception:
                response = f"{RESPONSE_MESSAGES['input_processing_error']}\n{self.format_selection_guide('hs6_code_selection_prompt')}"
                self.state.responses.append(response)
                return response

    def handle_hs10_selection(self, user_input: str) -> str:
        number_match = re.search(r'(\d+)', user_input)
        if number_match and self.state.hs10_candidates:
            selection = int(number_match.group(1))
            candidates = self.state.hs10_candidates
            if 1 <= selection <= len(candidates):
                selected = candidates[selection - 1]
                self.state.hs10_code = selected['code']
                country = self.state.country
                if not country or country.strip() == "":
                    country = DEFAULT_COUNTRY
                req = TariffPredictionRequest(
                    step=STEPS['hs10_select'],
                    hs10_code=selected['code'],
                    origin_country=country,
                    price=self.state.price,
                    quantity=self.state.quantity,
                    shipping_cost=self.state.shipping_cost,
                    scenario=self.state.scenario
                )
                resp: TariffPredictionResponse = tariff_prediction_step_api(req)
                
                # 관세 계산 완료 후 세션 정리
                self.reset_session()
                
                if resp.message and "📊 관세 계산 결과" in resp.message:
                    response = resp.message
                    self.state.responses.append(response)
                    return response
                elif resp.calculation_result:
                    response = resp.calculation_result.get('formatted_result', str(resp.calculation_result))
                    self.state.responses.append(response)
                    return response
                else:
                    response = resp.message or RESPONSE_MESSAGES['calculation_result_not_found']
                    self.state.responses.append(response)
                    return response
            else:
                response = f"{RESPONSE_MESSAGES['invalid_number']}\n\n{RESPONSE_MESSAGES['hs10_code_selection_prompt']}\n예시: \"1번\", \"2번\", \"3번\" 등"
                self.state.responses.append(response)
                return response
        else:
            response = f"{RESPONSE_MESSAGES['hs10_code_selection_prompt']}\n예시: \"1번\", \"2번\", \"3번\" 등"
            self.state.responses.append(response)
            return response 