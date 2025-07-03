from dataclasses import dataclass
from typing import List, Optional
from models.track_delivery.dto.progress_detail import ProgressDetail

@dataclass
class CargoProgressResult:
    success: bool
    progress_details: Optional[List[ProgressDetail]] = None
    error_reason: Optional[str] = None