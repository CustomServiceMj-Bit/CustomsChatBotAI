from app.dto.response import Response
from models.track_delivery.dto.request import TrackDeliveryRequest
from app.dependencies import track_delivery_handler

def run_model(question: str) -> "Response":
    """
        중앙 관리 모델을 통해 각 요청을 적절한 모델로 라우팅
        아무 모델과도 관계없는 경우 중앙 모델에서 적절한 응답을 생성해야 합니다.
        ex : "안녕, 너는 뭘 할 수 있어?"
        예시 코드는 아래와 같습니다.
    """
    # match domain:
    #     case "track_delivery":
    #         request = TrackDeliveryRequest(message=question)
    #         return track_delivery_handler.ask_to_gpt(request)
    #     case "관세예측":
    #         return
    #     case "통관 및 수입 문제 관련 답변":
    #         return
    #     case _:
    #         return

    request = TrackDeliveryRequest(message=question)
    return track_delivery_handler.ask_to_gpt(request)