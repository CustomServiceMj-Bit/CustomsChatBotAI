import os
import time
import requests
from typing import Dict, Any


class OpenAiClient:
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    def chat_completion(self, body: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for attempt in range(3):  # 1 initial + 2 retries
            response = requests.post(self.api_url, headers=headers, json=body)
            if response.status_code == 429 and attempt < 2:
                time.sleep(2)
                continue
            response.raise_for_status()
            return response.json()
