import os
import requests
from typing import Dict

from core.customs_tracking.dto.cargo_progress_result import CargoProgressResult
from core.customs_tracking.parser.unipass_xml_parser import parse_progress
from core.shared.constants.error_codes import (
    FETCH_ERROR_MESSAGE,
    INVALID_CARGO_NUMBER_MESSAGE,
    INVALID_BL_NUMBER_MESSAGE,
    NO_PROGRESS_INFO_MESSAGE,
)
from core.customs_tracking.api_spec.unipass_api_spec import (
    PARAM_API_KEY,
    PARAM_CARGO_NO,
    PARAM_HBL_NO,
    PARAM_MBL_NO,
    PARAM_BL_YEAR,
    CARGO_NO_PATTERN,
)


class UnipassCargoApiClient:
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    def get_cargo_progress_details_by_mt(self, cargo_mt_no: str) -> CargoProgressResult:
        cargo_mt_no = self._format_cargo_number(cargo_mt_no)
        if not self._is_valid_cargo_number(cargo_mt_no):
            return CargoProgressResult(success=False, error_reason=INVALID_CARGO_NUMBER_MESSAGE.message)

        query_params = {PARAM_CARGO_NO: cargo_mt_no}
        return self._get_cargo_progress_result(query_params)

    def get_cargo_progress_details_by_bl(self, hbl_no: str, mbl_no: str, year: str) -> CargoProgressResult:
        print(hbl_no, mbl_no, year)
        if not hbl_no or not mbl_no or not year:
            return CargoProgressResult(success=False, error_reason=INVALID_BL_NUMBER_MESSAGE.message)

        query_params = {
            PARAM_HBL_NO: hbl_no,
            PARAM_MBL_NO: mbl_no,
            PARAM_BL_YEAR: year
        }
        return self._get_cargo_progress_result(query_params)

    def _get_cargo_progress_result(self, query_params: Dict[str, str]) -> CargoProgressResult:
        url = self._build_request_url(query_params)
        xml = self._fetch_xml(url)

        try:
            parsed = parse_progress(xml)
        except Exception:
            return CargoProgressResult(success=False, error_reason=FETCH_ERROR_MESSAGE.message)

        if parsed and len(parsed) > 0:
            return CargoProgressResult(success=True, progress_details=parsed)
        else:
            return CargoProgressResult(success=False, error_reason=NO_PROGRESS_INFO_MESSAGE.message)

    def _is_valid_cargo_number(self, cargo_mt_no: str) -> bool:
        return bool(CARGO_NO_PATTERN.match(cargo_mt_no))

    def _build_request_url(self, query_params: Dict[str, str]) -> str:
        all_params = {PARAM_API_KEY: self.api_key, **query_params}
        return f"{self.api_url}?" + "&".join(f"{k}={v}" for k, v in all_params.items())

    def _fetch_xml(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _format_cargo_number(self, cargo_mt_no: str) -> str:
        return cargo_mt_no.replace("-", "").upper()
