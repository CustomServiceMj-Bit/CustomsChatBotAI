from app.dto.response import Response
from core.graphs.runner import run_customs_agent

def run_model(question: str) -> "Response":
    """
        중앙 관리 모델을 통해 각 요청을 적절한 모델로 라우팅
        아무 모델과도 관계없는 경우 중앙 모델에서 적절한 응답을 생성해야 합니다.
        ex : "안녕, 너는 뭘 할 수 있어?"
        예시 코드는 아래와 같습니다.
    """
    reply = run_customs_agent(question)
    return Response(
        reply=reply,
        success=True
    )