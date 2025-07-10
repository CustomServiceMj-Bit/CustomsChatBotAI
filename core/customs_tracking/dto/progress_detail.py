from dataclasses import dataclass

@dataclass(frozen=True)
class ProgressDetail:
    datetime: str
    status: str
    comment: str
