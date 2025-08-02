from app.dto.response import Response
from core.graphs.runner import run_customs_agent
from langchain_core.messages import HumanMessage, AIMessage

# 세션 맵: {session_id: messages}
session_map = {}

def run_model(question: str, session_id: str = None) -> "Response":
    # session_id가 없으면 대화내역 없이 동작
    if not session_id:
        messages = [HumanMessage(content=question)]
    else:
        # session_map에 없으면 빈 리스트 할당
        if session_id not in session_map:
            session_map[session_id] = []
        messages = session_map[session_id]
        messages.append(HumanMessage(content=question))

    # agent 실행 (messages를 넘김)
    state = run_customs_agent(question, session_id=session_id, messages=messages)

    # AI 응답 메시지 추가 (state["final_response"] 기준)
    ai_reply = state.get("final_response")
    if session_id and ai_reply:
        messages.append(AIMessage(content=ai_reply))
        session_map[session_id] = messages

    return Response(
        reply=ai_reply,
        progress_details=state.get("progress_details"),
        error_reason=state.get("error_reason"),
        success=True
    )