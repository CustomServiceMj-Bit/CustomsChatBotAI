from models.track_delivery.client.openai_client import OpenAiClient
from models.track_delivery.gpt.function_call_processor import FunctionCallProcessor
from models.track_delivery.gpt.gpt_message_factory import build_messages, build_request_body
from models.track_delivery.parser.gpt_response_parser import extract_message
from models.track_delivery.dto.request import TrackDeliveryRequest
from models.track_delivery.dto.cargo_progress_result import CargoProgressResult
from models.track_delivery.api_spec.openai_api_spec import GPT_3P5_TURBO, FUNC_AUTO_OPTION, FUNC_KEY
from models.common.error_codes import FETCH_ERROR_MESSAGE
from app.dto.response import Response


class TrackDeliveryHandler:
    def __init__(self, openai_client: OpenAiClient, function_call_processor: FunctionCallProcessor):
        self.openai_client = openai_client
        self.function_call_processor = function_call_processor

    def ask_to_gpt(self, request: TrackDeliveryRequest):
        user_message = build_messages(request.message, None)

        request_body = build_request_body(
            model=GPT_3P5_TURBO,
            user_messages=user_message,
            tool_choice=FUNC_AUTO_OPTION
        )

        gpt_response = self.openai_client.chat_completion(request_body)
        gpt_message = extract_message(gpt_response)

        if gpt_message is None:
            return Response.cargo_progres_result_to_response(
                CargoProgressResult(success=False, error_reason=FETCH_ERROR_MESSAGE)
            )
        elif FUNC_KEY in gpt_message:
            cargo_progress_result = self.function_call_processor.handle_function_call(gpt_message)
            return Response.cargo_progres_result_to_response(cargo_progress_result)
        else:
            reply = gpt_message.get("content")
            return Response.string_to_response(reply)