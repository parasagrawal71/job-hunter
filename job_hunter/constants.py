from enum import Enum


class JobCSVField(str, Enum):
    S_NO = "s_no"
    COMPANY = "company" 
    JOB_TITLE = "job_title"
    JOB_LINK = "job_link"
    YOE = "yoe"
    MATCH_PERCENTAGE = "match_percentage"
    MATCHED_KEYWORDS_COUNT = "matched_keywords_count"
    MATCHED_KEYWORDS = "matched_keywords"
    EXTRACTED_LOCATIONS = "extracted_locations"


class ErrorCSVField(str, Enum):
    COMPANY = "Company"
    ERROR = "Error"
    CAREER_URL = "Career URL"
