from typing import Optional, List

from pydantic import BaseModel

from core.customs_tracking.dto.progress_detail import ProgressDetail


class ModelResponse(BaseModel):
    reply: Optional[str] = None
    success: Optional[bool] = None
    progress_details: Optional[List[ProgressDetail]] = None
    error_reason: Optional[str] = None