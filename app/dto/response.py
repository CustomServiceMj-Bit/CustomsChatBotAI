from typing import List, Optional
from pydantic import BaseModel
from models.track_delivery.dto.progress_detail import ProgressDetail
from models.track_delivery.dto.cargo_progress_result import CargoProgressResult

class Response(BaseModel):
    reply: Optional[str] = None
    success: Optional[bool] = None
    progress_details: Optional[List[ProgressDetail]] = None
    error_reason: Optional[str] = None

    @staticmethod
    def cargo_progres_result_to_response(result: CargoProgressResult) -> "Response":
        return Response(
            success=result.success,
            error_reason=result.error_reason,
            progress_details=result.progress_details
        )

    @staticmethod
    def string_to_response(reply: str) -> "Response":
        return Response(reply=reply)