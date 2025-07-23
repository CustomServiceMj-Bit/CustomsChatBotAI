from core.tariff_prediction.agent.workflow import TariffPredictionWorkflow, workflow_manager
from core.shared.states.states import CustomsAgentState
from core.tariff_prediction.constants import RESPONSE_MESSAGES

def get_or_create_workflow(state: CustomsAgentState) -> TariffPredictionWorkflow:
    session_id = state.get("session_id")
    if session_id:
        return workflow_manager.get_session(session_id)
    else:
        return TariffPredictionWorkflow()  # 임시 워크플로우로 단발성 처리

def extract_context_from_messages(messages: list) -> str:
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
    return enhanced_context

def run_workflow_with_context(workflow: TariffPredictionWorkflow, state: CustomsAgentState, context: str) -> str:
    if context:
        enhanced_query = f"{context}\n\n{state['query']}"
        return workflow.process_user_input(enhanced_query)
    else:
        return workflow.process_user_input(state["query"])

def build_response_state(state: CustomsAgentState, response: str) -> CustomsAgentState:
    state["final_response"] = response
    # session_id는 외부에서 관리하므로 그대로 둠
    return state 