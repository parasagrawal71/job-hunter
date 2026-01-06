from datetime import datetime
import os

LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "ERROR": 40,
}

CURRENT_LOG_LEVEL = LOG_LEVELS["INFO"]  # default
# CURRENT_LOG_LEVEL = LOG_LEVELS["DEBUG"]  # debug

# 🔑 Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 🔑 Daily log file
LOG_FILE_PATH = os.path.join(
    LOG_DIR,
    f"log_{datetime.now().strftime('%Y_%m_%d')}.log",
)

def set_log_level(level: str):
    global CURRENT_LOG_LEVEL
    CURRENT_LOG_LEVEL = LOG_LEVELS.get(level.upper(), LOG_LEVELS["INFO"])


def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    # formatted = f"[{timestamp}] [{level}] {msg}"
    formatted = f"[{level}] {msg}"

    # File
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

    if LOG_LEVELS[level] < CURRENT_LOG_LEVEL:
        return

    # Console
    print(formatted)
