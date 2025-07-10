from http import HTTPStatus
from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorCode:
    http_status: HTTPStatus
    code: str
    message: str


INVALID_CARGO_NUMBER_MESSAGE = ErrorCode(
    http_status=HTTPStatus.BAD_REQUEST,
    code="TRACK-DELIVERY-001",
    message="화물 번호 형식이 올바르지 않습니다.",
)

NO_PROGRESS_INFO_MESSAGE = ErrorCode(
    http_status=HTTPStatus.NOT_FOUND,
    code="TRACK-DELIVERY-002",
    message="조회된 통관 진행 정보가 없습니다.",
)

FETCH_ERROR_MESSAGE = ErrorCode(
    http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
    code="TRACK-DELIVERY-003",
    message="통관 정보를 가져오는 중 예기치 못한 오류가 발생했습니다.",
)

INVALID_BL_NUMBER_MESSAGE = ErrorCode(
    http_status=HTTPStatus.BAD_REQUEST,
    code="TRACK-DELIVERY-004",
    message="BL 번호 형식이 올바르지 않습니다.",
)