from core.shared.states.states import CustomsAgentState

# 조건부 엣지 -> 라우팅 함수
def route_by_intent(state: CustomsAgentState) -> str:
    """의도에 따라 적절한 에이전트로 라우팅"""
    intent = state.get("intent")
    match intent:
        case "customs_tracking":
            return "customs_tracking"
        case "tariff_prediction":
            return "tariff_prediction"
        case "qna":
            return "qna"
        case _:
            return "qna"  # 기본값