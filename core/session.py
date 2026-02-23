import time
from datetime import datetime, timedelta
from typing import Optional
from utils.logger import SessionLogger
from config.settings import IDLE_THRESHOLD


class SessionManager:
    """Manages application sessions and idle detection"""
    
    def __init__(self):
        self.logger = SessionLogger()
        self.current_app: Optional[str] = None
        self.last_activity = time.time()
        self.is_idle = False
        
    def update_activity(self, app_name: str):
        """Update activity with current app"""
        current_time = time.time()
        
        # Check if we were idle
        if self.is_idle:
            self.is_idle = False
            self.logger.start_session(app_name)
            self.current_app = app_name
            
        # Check if app changed
        elif app_name != self.current_app:
            if self.current_app:
                self.logger.end_session()
            if app_name:
                self.logger.start_session(app_name)
            self.current_app = app_name
            
        self.last_activity = current_time
        
    def check_idle(self):
        """Check if system has become idle"""
        if not self.is_idle and self.current_app:
            idle_time = time.time() - self.last_activity
            if idle_time > IDLE_THRESHOLD:
                self.is_idle = True
                self.logger.log_idle()
                self.current_app = None
                return True
        return False
        
    def shutdown(self):
        """Clean shutdown - end current session"""
        if self.current_app:
            self.logger.end_session()