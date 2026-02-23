import os
from pathlib import Path

# Base Directions
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# File paths
DATA_FILE = DATA_DIR / "tracked_data.json"
SESSION_LOG_FILE = LOGS_DIR / "sessions.log"
USAGE_LOG_FILE = LOGS_DIR / "usage_log.txt"

# Monitoring Settigns
MONITOR_INTERVAL = 2
IDLE_THRESHOLD = 300