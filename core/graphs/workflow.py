from langgraph.graph import StateGraph
from langgraph.graph import END

from core.graphs.route import route_by_intent
from core.shared.states.states import CustomsAgentState
from core.qna.agent.qna_agent import qna_agent
from core.customs_tracking.agent.customs_tracking_agent import customs_tracking_agent
from core.tariff_prediction.agent.tariff_prediction_agent import tariff_prediction_agent
from core.shared.router.intent_router import  intent_router

def create_customs_graph():
    """관세청 에이전트 그래프를 생성합니다."""
    
    # 상태 그래프 초기화
    workflow = StateGraph(CustomsAgentState)
    
    # 노드 추가
    workflow.add_node("intent_router", intent_router)
    workflow.add_node("customs_tracking", customs_tracking_agent)
    workflow.add_node("tariff_prediction", tariff_prediction_agent)
    workflow.add_node("qna", qna_agent)
    
    # 시작점 설정
    workflow.set_entry_point("intent_router")
    
    # 조건부 엣지 설정
    workflow.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {
            "customs_tracking": "customs_tracking",
            "tariff_prediction": "tariff_prediction", 
            "qna": "qna"
        }
    )
    
    # 각 에이전트에서 종료점으로
    workflow.add_edge("customs_tracking", END)
    workflow.add_edge("tariff_prediction", END)
    workflow.add_edge("qna", END)
    
    return workflow.compile()