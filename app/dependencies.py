from models.track_delivery.client.openai_client import OpenAiClient
from models.track_delivery.gpt.function_call_processor import FunctionCallProcessor
from models.track_delivery.handler import TrackDeliveryHandler
from models.track_delivery.client.unipass_cargo_api_client import UnipassCargoApiClient
import os

# 의존성 구성 전용 클래스(?)
openai_client = OpenAiClient(
    api_key = os.getenv("OPENAI_API_KEY"),
    api_url = os.getenv("OPENAI_API_PATH")
)
unipass_cargo_api_client = UnipassCargoApiClient(
    api_key = os.getenv("UNIPASS_API_KEY"),
    api_url = os.getenv("UNIPASS_API_PATH")
)
function_call_processor = FunctionCallProcessor(unipass_cargo_api_client)
track_delivery_handler = TrackDeliveryHandler(openai_client, function_call_processor)