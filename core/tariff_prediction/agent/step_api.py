from core.tariff_prediction.dto.tariff_request import TariffPredictionRequest
from core.tariff_prediction.dto.tariff_response import TariffPredictionResponse
from core.tariff_prediction.tools.get_hs_classification import get_hs_classification
from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result, generate_hs10_candidates
from core.tariff_prediction.tools.calculate_tariff_amount import calculate_tariff_amount
from core.tariff_prediction.tools.parse_tariff_result import parse_tariff_result
from core.shared.utils.llm import get_llm
from core.tariff_prediction.constants import LLM_PROMPT_TEMPLATES, STEP_API

def tariff_prediction_step_api(req: TariffPredictionRequest) -> TariffPredictionResponse:
    step = req.step
    if not step or step == STEP_API['AUTO_STEP']:
        llm = get_llm()
        user_input = req.product_description or req.hs6_code or req.hs10_code or ''
        step_prompt = LLM_PROMPT_TEMPLATES['step_classification'].format(user_input=user_input)
        step_result = llm.invoke([{"role": "system", "content": step_prompt}])
        step = str(getattr(step_result, 'content', step_result)).strip()
    if step == STEP_API['INPUT_STEP']:
        # 상품 설명 → HS6 후보 예측
        hs6_result = get_hs_classification(req.product_description)
        hs6_candidates = parse_hs6_result(hs6_result)
        return TariffPredictionResponse(
            step=STEP_API['HS6_SELECT_STEP'],
            hs6_candidates=hs6_candidates,
            message=STEP_API['HS6_SELECTION_MESSAGE']
        )
    elif step == STEP_API['HS6_SELECT_STEP']:
        # HS6 코드 → HS10 후보 추출
        hs10_candidates = generate_hs10_candidates(req.hs6_code)
        return TariffPredictionResponse(
            step=STEP_API['HS10_SELECT_STEP'],
            hs10_candidates=hs10_candidates,
            message=STEP_API['HS10_SELECTION_MESSAGE']
        )
    elif step == STEP_API['HS10_SELECT_STEP']:
        # HS10 코드, 국가, 가격 등 입력받아 관세 계산
        result = calculate_tariff_amount.invoke({
            "product_code": req.hs10_code,
            "value": req.price,
            "origin_country": req.origin_country,
            "item_count": req.quantity,
            "shipping_cost": req.shipping_cost,
            "situation": req.scenario
        })
    
        # 결과를 문자열로 변환
        result_str = str(result)
        
        if any(keyword in result_str for keyword in STEP_API['ERROR_KEYWORDS']):
            return TariffPredictionResponse(
                step=STEP_API['RESULT_STEP'],
                calculation_result=None,
                message=result_str
            )
        else:
            parsed_result = parse_tariff_result(result_str)
            formatted_result = parsed_result['formatted_result']
            
            return TariffPredictionResponse(
                step=STEP_API['RESULT_STEP'],
                calculation_result=parsed_result, 
                message=formatted_result
            )
    else:
        return TariffPredictionResponse(
            step=STEP_API['HS6_SELECT_STEP'],
            message=STEP_API['DEFAULT_ERROR_MESSAGE']
        ) 