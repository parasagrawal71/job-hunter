from dataclasses import dataclass
from typing import List


@dataclass
class Job:
    company: str
    title: str
    link: str
    yoe: int | None
    matched_keywords: List[str]
    keyword_count: int
    match_percentage: float
    matched_locations: List[str]  # ✅ ADD THIS
