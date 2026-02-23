import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from config.settings import SESSION_LOG_FILE, USAGE_LOG_FILE

class SessionLogger:
    """Handles session logging for applications"""

    def __init__(self):
        self.session_log = logging.getLogger('session')
        self.session_log.setLevel(logging.INFO)

        # File handler for session log
        fh = logging.FileHandler(SESSION_LOG_FILE)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        fh.setFormatter(formatter)
        self.session_log.addHandler(fh)

        # Also setup usage logger
        self.usage_log = logging.getLogger('usage')
        self.usage_log.setLevel(logging.INFO)
        fh_usage = logging.FileHandler(USAGE_LOG_FILE)
        fh_usage.setLevel(logging.INFO)
        fh_usage.setFormatter(formatter)
        self.usage_log.addHandler(fh_usage)

        self.current_session = None
        self.session_start = None

    def start_session(self, app_name: str):
        """Start a new session for an app"""
        self.current_session = app_name
        self.session_start = datetime.now()
        self.session_log.info(f"SESSION_START - {app_name}")

    def end_session(self):
        """End current session"""
        if self.current_session and self.session_start:
            duration = (datetime.now() - self.session_start).total_seconds()
            self.session_log.info(
                f"SESSION_END - {self.current_session} - Duration: {duration:.0f}s"
            )
            self.usage_log.info(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
                f"{self.current_session} - {duration:.0f}s"
            )
            self.current_session = None
            self.current_start = None

    def log_idle(self):
        """Log when system becomes idle"""
        if self.current_session:
            self.session_log.info(f"IDLE_START - {self.current_session}")
            self.end_session()

            