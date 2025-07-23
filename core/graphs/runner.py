from langchain_core.messages import HumanMessage

from core.graphs.workflow import create_customs_graph
from core.shared.states.states import CustomsAgentState


def run_customs_agent(query: str, session_id: str = None, messages=None) -> CustomsAgentState:
    """관세청 에이전트를 실행합니다."""
    
    # 그래프 생성
    app = create_customs_graph()
    
    # messages가 없으면 query만 포함
    if messages is None:
        messages = [HumanMessage(content=query)]

    # 초기 상태 설정
    initial_state = CustomsAgentState(
        messages=messages,
        query=query,
        intent=None,
        final_response="",
        intermediate_results={},
        error_reason=None,
        progress_details=None
    )
    
    # 그래프 실행
    result = app.invoke(initial_state)
    
    return result