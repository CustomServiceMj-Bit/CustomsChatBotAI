

import json
from typing import Any, Dict

from models.track_delivery.client.unipass_cargo_api_client import UnipassCargoApiClient
from models.track_delivery.dto.cargo_progress_result import CargoProgressResult
from models.track_delivery.api_spec.openai_api_spec import FUNC_KEY
from models.common.error_codes import FETCH_ERROR_MESSAGE


class FunctionCallProcessor:
    def __init__(self, unipass_cargo_api_client: UnipassCargoApiClient):
        self.unipass_cargo_api_client = unipass_cargo_api_client

    def handle_function_call(self, gpt_message: Dict[str, Any]) -> CargoProgressResult:
        try:
            function_call = gpt_message.get(FUNC_KEY, {})
            function_name = function_call.get("name")
            arguments = function_call.get("arguments", "{}")

            args: Dict[str, str] = json.loads(arguments)

            print(function_name)

            if function_name == "trackByCargoMtNo":
                tracking_no = args.get("cargoMtNo")
                return self.unipass_cargo_api_client.get_cargo_progress_details(tracking_no)

            elif function_name == "trackByBlInfo":
                hbl_no = args.get("hBlNo")
                mbl_no = args.get("mBlNo")
                year = args.get("year")
                return self.unipass_cargo_api_client.get_cargo_progress_details(hbl_no, mbl_no, year)

            else:
                return CargoProgressResult(
                    success=False,
                    error_reason=FETCH_ERROR_MESSAGE.message
                )

        except Exception:
            return CargoProgressResult(
                success=False,
                error_reason=FETCH_ERROR_MESSAGE.message
            )