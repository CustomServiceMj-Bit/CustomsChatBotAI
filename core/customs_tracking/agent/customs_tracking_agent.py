from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from core.customs_tracking.tools.get_cargo_progress_details import get_cargo_progress_details_by_bl, get_cargo_progress_details_by_mt
from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm


def customs_tracking_agent(state: CustomsAgentState) -> CustomsAgentState:
    tools = [get_cargo_progress_details_by_mt, get_cargo_progress_details_by_bl]  # function calling
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        당신은 통관 및 배송 추적 전문가입니다.
        사용할 수 있는 도구 목록이 아래 제공됩니다.
        
        다음 사용자 쿼리를 분석하여 정확히 하나의 카테고리로 분류해주세요:
        1. get_cargo_progress_details_by_mt: 화물번호를 통한 통관 진행 조회
        2. get_cargo_progress_details_by_bl: 연도, MBL, HBL 번호를 통한 통관 진행 조회

        도구를 이용해 통관 상태를 확인하고, 호출 결과는 가공하지 말고 그대로 반환하세요.
        """),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "{agent_scratchpad}"),
    ])
    agent = create_openai_functions_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    result = agent_executor.invoke({
        "input": state["query"],
        "messages": state["messages"]
    })

    state["final_response"] = result["output"]
    return state