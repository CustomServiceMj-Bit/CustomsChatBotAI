from core.tariff_prediction.dto.tariff_request import TariffPredictionRequest
from core.tariff_prediction.dto.tariff_response import TariffPredictionResponse
from core.tariff_prediction.tools.get_hs_classification import get_hs_classification
from core.tariff_prediction.tools.parse_hs_results import parse_hs6_result, generate_hs10_candidates
from core.tariff_prediction.tools.calculate_tariff_amount import calculate_tariff_amount
from core.tariff_prediction.tools.parse_tariff_result import parse_tariff_result
from core.shared.utils.llm import get_llm

def tariff_prediction_step_api(req: TariffPredictionRequest) -> TariffPredictionResponse:
    step = req.step
    # Step 자동 분류: step이 'auto'이거나 비어 있으면 LLM으로 분류
    if not step or step == 'auto':
        llm = get_llm()
        step_prompt = f"""
        다음 사용자 입력이 관세 예측 플로우의 어떤 단계에 해당하는지 분류하세요.
        - 상품 설명 입력: input
        - HS6 코드 선택: hs6_select
        - HS10 코드 선택 및 관세 계산: hs10_select
        반드시 input, hs6_select, hs10_select 중 하나로만 답하세요.
        사용자 입력: {req.product_description or req.hs6_code or req.hs10_code or ''}
        """
        step_result = llm.invoke([{"role": "system", "content": step_prompt}])
        step = str(getattr(step_result, 'content', step_result)).strip()
    # Step별 분기
    if step == "input":
        # 상품 설명 → HS6 후보 예측
        hs6_result = get_hs_classification(req.product_description)
        hs6_candidates = parse_hs6_result(hs6_result)
        return TariffPredictionResponse(
            step="hs6_select",
            hs6_candidates=hs6_candidates,
            message="상품에 해당하는 HS6 코드를 선택해 주세요."
        )
    elif step == "hs6_select":
        # HS6 코드 → HS10 후보 추출
        hs10_candidates = generate_hs10_candidates(req.hs6_code)
        return TariffPredictionResponse(
            step="hs10_select",
            hs10_candidates=hs10_candidates,
            message="HS10 코드 후보를 선택해 주세요."
        )
    elif step == "hs10_select":
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
        
        # 에러 메시지인지 확인 (에러 메시지는 보통 짧고 특정 키워드를 포함)
        if result_str.startswith("오류") or result_str.startswith("Error") or "실패" in result_str or "오류" in result_str:
            # 에러 메시지
            return TariffPredictionResponse(
                step="result",
                calculation_result=None,
                message=result_str
            )
        else:
            # 성공적인 결과 - 예쁘게 포맷팅
            parsed_result = parse_tariff_result(result_str)
            formatted_result = parsed_result['formatted_result']
            
            return TariffPredictionResponse(
                step="result",
                calculation_result=parsed_result,  # 딕셔너리 형태로 전달
                message=formatted_result  # 포맷팅된 결과를 message에 전달
            )
    else:
        return TariffPredictionResponse(
            step="hs6_select",
            message="잘못된 요청입니다. 상품 설명을 입력해 주세요."
        ) 