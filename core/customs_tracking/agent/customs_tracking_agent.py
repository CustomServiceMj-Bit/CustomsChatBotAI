from langchain.agents import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

from core.qna.tools.get_cargo_progress_details import get_cargo_progress_details_by_bl, get_cargo_progress_details_by_mt
from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm


def customs_tracking_agent(state: CustomsAgentState) -> CustomsAgentState:
    tools = [get_cargo_progress_details_by_mt, get_cargo_progress_details_by_bl]  # function calling
    llm = get_llm()

    system_message = SystemMessage(
        content="""
    당신은 통관 및 배송 추적 전문가입니다.
아래와 같은 작업을 수행할 수 있는 두 가지 도구가 있습니다:
1. get_clearance_status: 운송장 번호로 통관 상태를 조회합니다.
2. track_shipment: 운송장 번호로 배송 경로를 조회합니다.

사용자가 운송장 번호를 입력하면 **통관 상태와 배송 정보 모두** 제공하세요.
두 도구 모두를 사용해 정보를 수집한 후 종합적인 답변을 작성하세요.
    """)
    react_agent = create_react_agent(llm, tools)

    messages = [system_message, HumanMessage(content=state["query"])]
    result = react_agent.invoke({"messages": messages})

    state["final_response"] = result["messages"][-1].content
    return state