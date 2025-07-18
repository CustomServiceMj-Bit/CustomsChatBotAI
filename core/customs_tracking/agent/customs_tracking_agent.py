from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from core.customs_tracking.dto.cargo_progress_result import CargoProgressResult
from core.customs_tracking.tools.get_cargo_progress_details import get_cargo_progress_details_by_bl, get_cargo_progress_details_by_mt
from core.shared.states.states import CustomsAgentState
from core.shared.utils.llm import get_llm


def customs_tracking_agent(state: CustomsAgentState) -> CustomsAgentState:
    tools = [get_cargo_progress_details_by_mt, get_cargo_progress_details_by_bl]  # function calling
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """ 당신은 통관 진행 조회 서비스를 사용자에게 직접 제공하는 관세청 도우미입니다.
        아래 도구를 통해 실제 통관 진행 정보를 조회할 수 있으므로, 가능한 경우에는 반드시 도구를 사용하세요.
        
        도구 목록:
        1. get_cargo_progress_details_by_mt: 화물번호를 통한 통관 진행 조회
        2. get_cargo_progress_details_by_bl: 연도, MBL, HBL 번호를 통한 통관 진행 조회
        
        사용자의 질문이 화물번호나 BL 정보를 포함하지 않은 경우에는 다음 문장으로 안내하세요:
        "통관 진행을 조회하기 위해서는 화물번호 또는 BL 번호가 필요합니다. 화물번호(MT 번호) 또는 연도, MBL, HBL 번호를 제공해 주시면 통관 진행 정보를 조회해 드리겠습니다."
        """),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "{agent_scratchpad}"),
    ])
    agent = create_openai_functions_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    print(prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    result = agent_executor.invoke({
        "input": state["query"],
        "messages": state["messages"]
    })

    steps = result.get("intermediate_steps", [])
    if steps:
        _, tool_result = steps[-1]
        # tool_result가 dict라면 아래처럼 처리
        if isinstance(tool_result, CargoProgressResult):
            state["progress_details"] = tool_result.progress_details
            state["error_reason"] = tool_result.error_reason
        else:
            state["progress_details"] = None
            state["error_reason"] = None

        state["final_response"] = ""
    else:
        print(result["output"])
        state["final_response"] = result["output"]

    return state