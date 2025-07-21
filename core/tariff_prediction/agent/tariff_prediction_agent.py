from typing import Dict, Any, List
import re

from core.shared.states.states import CustomsAgentState
from core.tariff_prediction.tools.calculate_tariff_amount import calculate_tariff_amount
from core.tariff_prediction.tools.detect_scenario import detect_scenario_from_input
from core.tariff_prediction.tools.parse_user_input import parse_user_input
from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result, generate_hs10_candidates
from core.tariff_prediction.tools.parse_tariff_result import parse_tariff_result
from core.tariff_prediction.constants import (
    SUPPORTED_COUNTRIES, OFF_TOPIC_KEYWORDS, CORRECTION_KEYWORDS, 
    SESSION_TERMINATION_KEYWORDS, SIMPLE_TARIFF_REQUESTS, 
    TARIFF_CONTEXT_KEYWORDS, DEFAULT_EXCHANGE_RATES,
    DEFAULT_COUNTRY, DEFAULT_QUANTITY, DEFAULT_SHIPPING_COST, DEFAULT_SESSION_ID,
    ERROR_MESSAGES, CORRECTION_MESSAGES, RESPONSE_MESSAGES, STATE_KEYS, STEPS, LLM_PROMPTS
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
        if session_id not in self.sessions:
            self.sessions[session_id] = TariffPredictionWorkflow()
        return self.sessions[session_id]
    def cleanup_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

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
            'responses': [],
            'predicted_scenario': None,
            'last_user_input': None
        }
        
        self.supported_countries = SUPPORTED_COUNTRIES

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
            'responses': [],
            'predicted_scenario': None,
            'last_user_input': None
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
                return RESPONSE_MESSAGES['hs10_reprediction_not_available']
        
        return ""

    def is_off_topic(self, user_input: str) -> bool:
        """관세 계산과 관련 없는 주제인지 확인합니다."""
        input_lower = user_input.lower()
        return any(keyword in input_lower for keyword in OFF_TOPIC_KEYWORDS)

    def process_user_input(self, user_input: str) -> str:
        current_query = user_input
        if "이전 대화:" in user_input and "현재 질문:" in user_input:
            parts = user_input.split("현재 질문:")
            if len(parts) > 1:
                current_query = parts[1].strip()
        
        if any(word in current_query for word in SESSION_TERMINATION_KEYWORDS):
            self.reset_session()
            return ERROR_MESSAGES['session_terminated']

        if self.state['session_active']:
            has_tariff_context = any(keyword in user_input.lower() for keyword in TARIFF_CONTEXT_KEYWORDS)
            
            if not has_tariff_context and self.is_off_topic(current_query):
                return RESPONSE_MESSAGES['off_topic_warning']

        correction_response = self.handle_correction_request(current_query)
        if correction_response:
            return correction_response

        if self.state['current_step'] == 'hs6_selection':
            pass

        if current_query.strip() in SIMPLE_TARIFF_REQUESTS:
            return RESPONSE_MESSAGES['simple_tariff_request']

        if self.state['current_step'] == 'scenario_selection':
            return self.handle_scenario_selection(current_query)
        elif self.state['current_step'] == 'input_collection':
            return self.handle_input_collection(current_query)
        elif self.state['current_step'] == 'hs6_selection':
            return self.handle_hs6_selection(current_query)
        elif self.state['current_step'] == 'hs10_selection':
            return self.handle_hs10_selection(current_query)

        return RESPONSE_MESSAGES['unrecognized_state']

    def handle_scenario_selection(self, user_input: str) -> str:
        detected_scenario = self.detect_scenario_from_input(user_input)
        if detected_scenario:
            self.state['scenario'] = detected_scenario
            self.state['current_step'] = 'input_collection'
            self.state['session_active'] = True
            response = RESPONSE_MESSAGES['input_collection_prompt']
            self.state['responses'].append(response)
            return response
        
        self.state['current_step'] = 'input_collection'
        self.state['session_active'] = True
        response = RESPONSE_MESSAGES['input_collection_prompt']
        self.state['responses'].append(response)
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
        if not self.state.get('scenario'):
            predicted = self.detect_scenario_from_input(user_input)
            if predicted:
                self.state['scenario'] = predicted
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
            self.state['responses'].append(response)
            return response
        price = parsed['price']
        price_unit = parsed.get('price_unit', '원')
        if price_unit != '원':
            try:
                from core.tariff_prediction.tools.get_exchange_rate_info import get_exchange_rate_api
                exchange_rate = get_exchange_rate_api(price_unit, self.state.get('scenario', '해외직구'))
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
        self.state.update(parsed)
        self.state['price'] = price
        self.state['price_unit'] = price_unit
        req = TariffPredictionRequest(
            step=STEPS['input'],
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
        self.state['current_step'] = STEPS['hs6_selection']
        scenario_str = self.state.get('scenario', '')
        scenario_guide = f"{self.josa_으로(scenario_str)} {RESPONSE_MESSAGES['scenario_guide_prefix']}\n\n" if scenario_str else ""
        price_display = f"{price:,.0f}원"
        if price_unit != '원' and parsed.get('price_unit') != '원':
            original_price = parsed.get('price', price)
            original_unit = parsed.get('price_unit', price_unit)
            price_display = f"{original_price} {original_unit} ({price:,.0f}원)"
        response = scenario_guide + f"상품묘사: {parsed['product_name']}\n국가: {parsed['country']}\n가격: {price_display}\n수량: {parsed.get('quantity', 1)}개\n\n{RESPONSE_MESSAGES['hs6_code_prediction_prompt']}\n" + '\n'.join([
                            f"{i+1}. {c['description']} ({RESPONSE_MESSAGES['hs6_confidence']} {c['confidence']:.1%})" for i, c in enumerate(resp.hs6_candidates or [])
        ]) + f"\n\n{self.format_selection_guide('hs6_code_selection_prompt')}"
        self.state['responses'].append(response)
        return response

    def parse_hs6_result(self, hs6_result: str) -> List[Dict]:
        """HS6 결과를 파싱합니다."""
        return parse_hs6_result(hs6_result)

    def format_hs6_candidates(self) -> str:
        """HS6 후보를 포맷팅합니다."""
        formatted = ""
        for i, candidate in enumerate(self.state['hs6_candidates'], 1):
            formatted += f"{i}. {candidate['code']} - {candidate['description']} ({RESPONSE_MESSAGES['hs6_confidence']} {candidate['confidence']:.1%})\n"
        return formatted

    def format_selection_guide(self, selection_prompt_key: str) -> str:
        """번호 선택 안내 + 예시 + 재예측 안내를 포맷팅합니다."""
        return (
            f"{RESPONSE_MESSAGES[selection_prompt_key]}\n"
            f"{RESPONSE_MESSAGES['number_example']}\n"
            f"{RESPONSE_MESSAGES['reprediction_guide']}"
        )

    def handle_hs6_selection(self, user_input: str) -> str:
        from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result
        from core.shared.utils.llm import get_llm
        
        number_match = re.search(r'(\d+)', user_input)
        
        if number_match and self.state.get('hs6_candidates'):
            selection = int(number_match.group(1))
            candidates = self.state['hs6_candidates']
            if 1 <= selection <= len(candidates):
                selected = candidates[selection - 1]
                self.state['hs6_code'] = selected['code']
                req = TariffPredictionRequest(
                    step=STEPS['hs6_select'],
                    hs6_code=selected['code']
                )
                resp: TariffPredictionResponse = tariff_prediction_step_api(req)
                if resp.message and (not resp.hs10_candidates):
                    self.state['responses'].append(resp.message)
                    return resp.message
                self.state['hs10_candidates'] = resp.hs10_candidates
                self.state['current_step'] = STEPS['hs10_selection']
                response = f"{RESPONSE_MESSAGES['hs6_code_selected']} {selected['code']}\n\n{RESPONSE_MESSAGES['hs10_code_prediction_prompt']}\n" + '\n'.join([
                    f"{i+1}. {c['code']} - {c['description']}" for i, c in enumerate(resp.hs10_candidates or [])
                ]) + f"\n\n{self.format_selection_guide('hs10_code_selection_prompt')}"
                self.state['responses'].append(response)
                return response
            else:
                response = self.format_selection_guide('hs6_code_selection_prompt')
                self.state['responses'].append(response)
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
                    self.state['responses'].append(response)
                    return response
                    
            except Exception:
                response = f"{RESPONSE_MESSAGES['input_processing_error']}\n{self.format_selection_guide('hs6_code_selection_prompt')}"
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
        number_match = re.search(r'(\d+)', user_input)
        
        if number_match and self.state.get('hs10_candidates'):
            selection = int(number_match.group(1))
            candidates = self.state['hs10_candidates']
            if 1 <= selection <= len(candidates):
                selected = candidates[selection - 1]
                self.state['hs10_code'] = selected['code']
                country = self.state.get('country', DEFAULT_COUNTRY)
                if not country or country.strip() == "":
                    country = DEFAULT_COUNTRY
                
                req = TariffPredictionRequest(
                    step=STEPS['hs10_select'],
                    hs10_code=selected['code'],
                    origin_country=country,
                    price=self.state.get('price'),
                    quantity=self.state.get('quantity', 1),
                    shipping_cost=self.state.get('shipping_cost', 0),
                    scenario=self.state.get('scenario')
                )
                resp: TariffPredictionResponse = tariff_prediction_step_api(req)
                self.reset_session()
                if resp.message and "📊 관세 계산 결과" in resp.message:
                    response = resp.message
                    self.state['responses'].append(response)
                    return response
                elif resp.calculation_result:
                    response = resp.calculation_result.get('formatted_result', str(resp.calculation_result))
                    self.state['responses'].append(response)
                    return response
                else:
                    response = resp.message or RESPONSE_MESSAGES['calculation_result_not_found']
                    self.state['responses'].append(response)
                    return response
            else:
                response = f"{RESPONSE_MESSAGES['invalid_number']}\n\n{RESPONSE_MESSAGES['hs10_code_selection_prompt']}\n예시: \"1번\", \"2번\", \"3번\" 등"
                self.state['responses'].append(response)
                return response
        else:
            response = f"{RESPONSE_MESSAGES['hs10_code_selection_prompt']}\n예시: \"1번\", \"2번\", \"3번\" 등"
            self.state['responses'].append(response)
            return response



    def _perform_hs6_reprediction(self, user_input: str) -> str:
        from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result
        from core.shared.utils.llm import get_llm
        product_name = self.state.get('product_name')
        if not product_name or not isinstance(product_name, str) or not product_name.strip():
            response = RESPONSE_MESSAGES['product_name_not_available']
            self.state['responses'].append(response)
            return response
        try:
            reprediction_prompt = f"{LLM_PROMPTS['hs6_reprediction_prompt']}\n\n{LLM_PROMPTS['product_name']}: {product_name}\n{LLM_PROMPTS['user_additional_opinion']}: {user_input}\n\n{LLM_PROMPTS['hs6_reprediction_format']}\n{LLM_PROMPTS['hs6_reprediction_example']}"
            llm = get_llm()
            hs6_response = llm.invoke([{"role": "user", "content": reprediction_prompt}])
            hs6_result = extract_llm_response(hs6_response)
            if not hs6_result or len(hs6_result.strip()) < 10:
                response = RESPONSE_MESSAGES['hs6_code_prediction_failed']
                self.state['responses'].append(response)
                return response
            try:
                hs6_candidates = parse_hs6_result(hs6_result)
            except Exception:
                response = RESPONSE_MESSAGES['hs6_code_prediction_processing_error']
                self.state['responses'].append(response)
                return response
            if not hs6_candidates:
                response = RESPONSE_MESSAGES['hs6_code_prediction_failed']
                self.state['responses'].append(response)
                return response
            self.state['hs6_candidates'] = hs6_candidates
            scenario_str = self.state.get('scenario', '')
            scenario_guide = f"{self.josa_으로(scenario_str)} {RESPONSE_MESSAGES['scenario_guide_prefix']}\n\n" if scenario_str else ""
            response = scenario_guide + f"상품묘사: {product_name}\n국가: {self.state.get('country','')}\n가격: {self.state.get('price',0):,}원\n수량: {self.state.get('quantity',1)}개\n\n{RESPONSE_MESSAGES['hs6_code_reprediction_result']}\n" + '\n'.join([
                f"{i+1}. {c['description']} ({RESPONSE_MESSAGES['hs6_confidence']} {c['confidence']:.1%})" for i, c in enumerate(hs6_candidates)
            ]) + f"\n\n{RESPONSE_MESSAGES['hs6_code_selection_prompt']}\n예시: \"1번\", \"2번\", \"3번\" 등"
            self.state['responses'].append(response)
            return response
        except Exception:
            response = RESPONSE_MESSAGES['hs6_code_reprediction_error']
            self.state['responses'].append(response)
            return response

    def _perform_hs10_reprediction(self, user_input: str) -> str:
        from core.tariff_prediction.tools.parse_hs_results import generate_hs10_candidates
        from core.shared.utils.llm import get_llm
        
        hs6_code = self.state.get('hs6_code')
        if not hs6_code:
            response = RESPONSE_MESSAGES['hs6_code_not_available']
            self.state['responses'].append(response)
            return response
        
        try:
            hs10_candidates = generate_hs10_candidates(hs6_code)
            
            if not hs10_candidates:
                response = RESPONSE_MESSAGES['hs10_code_prediction_failed']
                self.state['responses'].append(response)
                return response
            
            self.state['hs10_candidates'] = hs10_candidates
            
            response = f"{STATE_KEYS['hs6_code']}: {hs6_code}\n\n{RESPONSE_MESSAGES['hs10_code_reprediction_result']}\n" + '\n'.join([
                f"{i+1}. {c['code']} - {c['description']}" for i, c in enumerate(hs10_candidates)
            ]) + f"\n\n{RESPONSE_MESSAGES['hs10_code_selection_prompt']}\n예시: \"1번\", \"2번\", \"3번\" 등"
            
            self.state['responses'].append(response)
            return response
            
        except Exception:
            response = RESPONSE_MESSAGES['hs10_code_reprediction_error']
            self.state['responses'].append(response)
            return response

    def perform_calculation(self) -> str:
        try:
            tariff_result = calculate_tariff_amount(
                product_code=self.state['hs10_code'],
                value=self.state['price'],
                origin_country=self.state['country'],
                item_count=self.state['quantity'],
                shipping_cost=self.state['shipping_cost'],
                situation=self.state['scenario']
            )
            
            friendly_result = self.generate_friendly_result(tariff_result)
            
            self.reset_session()
            
            return friendly_result
            
        except Exception as e:
            self.reset_session()
            return f"{ERROR_MESSAGES['calculation_error']} {str(e)}"

    def generate_friendly_result(self, tariff_result: str) -> str:
        parsed_result = self.parse_tariff_result(tariff_result)
        
        product_name = self.state.get('product_name', RESPONSE_MESSAGES['product_name_placeholder'])
        country = self.state.get('country', RESPONSE_MESSAGES['country_placeholder'])
        price = self.state.get('price', 0)
        scenario = self.state.get('scenario', RESPONSE_MESSAGES['scenario_placeholder'])
        
        friendly_message = f"""# 🎯 {RESPONSE_MESSAGES['tariff_calculation_complete']}!

## 📦 {RESPONSE_MESSAGES['product_info']}
- **{STATE_KEYS['product_name']}**: {product_name}
- **{STATE_KEYS['country']}**: {country}
- **{STATE_KEYS['price']}**: {price:,}원
- **{STATE_KEYS['scenario']}**: {scenario}

## 📊 {RESPONSE_MESSAGES['calculation_result']}
{parsed_result['formatted_result']}

## 💡 {RESPONSE_MESSAGES['note']}
- {RESPONSE_MESSAGES['tariff_note_1']}
- {RESPONSE_MESSAGES['tariff_note_2']}
- {RESPONSE_MESSAGES['tariff_note_3']}
        """
        
        return friendly_message

    def parse_tariff_result(self, tariff_result: str) -> Dict[str, Any]:
        return parse_tariff_result(tariff_result)
    


def tariff_prediction_agent(state: CustomsAgentState) -> CustomsAgentState:
    session_id = state.get("session_id")
    if session_id:
        workflow = workflow_manager.get_session(session_id)
    else:
        workflow = None
    messages = state.get("messages", [])
    context = ""
    previous_llm_responses = []
    if messages:
        recent_messages = messages[-10:]
        user_messages = []
        for msg in recent_messages:
            if hasattr(msg, 'type'):
                if msg.type == 'human':
                    user_messages.append(msg.content)
                elif msg.type == 'ai':
                    if hasattr(msg, 'content') and isinstance(msg.content, str):
                        content = msg.content
                        if any(keyword in content for keyword in ['HS6 코드 후보', 'HS10 코드 후보', '번호를 선택']):
                            previous_llm_responses.append(content)
        if user_messages:
            context = " ".join(user_messages[-5:])
    enhanced_context = context or ""
    if previous_llm_responses:
        enhanced_context += f"\n\n{RESPONSE_MESSAGES['previous_llm_response']}\n" + "\n".join(previous_llm_responses[-2:])
    if workflow:
        if enhanced_context:
            enhanced_query = f"{enhanced_context}\n\n{state['query']}"
            response = workflow.process_user_input(enhanced_query)
        else:
            response = workflow.process_user_input(state["query"])
    else:
        response = ERROR_MESSAGES.get('session_error', '세션이 유효하지 않습니다.')
    state["final_response"] = response
    state["session_id"] = session_id
    return state