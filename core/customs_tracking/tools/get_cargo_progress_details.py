from langchain_core.tools import tool

from dependencies import unipass_cargo_api_client
from core.customs_tracking.dto.cargo_progress_result import CargoProgressResult

@tool
def get_cargo_progress_details_by_mt(cargo_mt_no: str) -> CargoProgressResult:
    """운송장 번호로 해당 물품의 통관 상태를 조회합니다."""
    result = unipass_cargo_api_client.get_cargo_progress_details_by_mt(cargo_mt_no)
    return result

@tool
def get_cargo_progress_details_by_bl(hbl_no: str, mbl_no: str, year: str) -> CargoProgressResult:
    """
        BL 번호로 해당 물품의 통관 상태를 조회합니다.
    """
    result = unipass_cargo_api_client.get_cargo_progress_details_by_bl(hbl_no=hbl_no, mbl_no=mbl_no, year=year)
    return result