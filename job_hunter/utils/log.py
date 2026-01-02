
from datetime import datetime

LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "ERROR": 40,
}

CURRENT_LOG_LEVEL = LOG_LEVELS["INFO"]  # default
# CURRENT_LOG_LEVEL = LOG_LEVELS["DEBUG"]  # debug


def set_log_level(level: str):
    global CURRENT_LOG_LEVEL
    CURRENT_LOG_LEVEL = LOG_LEVELS.get(level.upper(), LOG_LEVELS["INFO"])


def log(msg: str, level: str = "INFO"):
    if LOG_LEVELS[level] < CURRENT_LOG_LEVEL:
        return
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")