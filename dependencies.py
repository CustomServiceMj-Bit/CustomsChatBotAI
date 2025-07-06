import os

from core.customs_tracking.client.unipass_cargo_api_client import UnipassCargoApiClient

# 의존성 구성 전용 클래스(?)
# openai_client = OpenAiClient(
#     api_key = os.getenv("OPENAI_API_KEY"),
#     api_url = os.getenv("OPENAI_API_PATH")
# )
unipass_cargo_api_client = UnipassCargoApiClient(
    api_key = os.getenv("UNIPASS_API_KEY"),
    api_url = os.getenv("UNIPASS_API_PATH")
)