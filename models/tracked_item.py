from datetime import datetime
from typing import Dict, Optional


class TrackedItem:
    """Model representing a tracked application or website"""
    
    def __init__(self, name: str, limit_minutes: int):
        self.name = name.lower()
        self.limit_minutes = limit_minutes
        self.used_seconds = 0
        self.daily_log: Dict[str, int] = {}
        self.notified = False
        self.is_active = False
        self.last_active_time: Optional[datetime] = None
        self.first_seen = datetime.now().isoformat()
        
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "limit": self.limit_minutes,
            "used": self.used_seconds,
            "log": self.daily_log,
            "notified": self.notified,
            "first_seen": self.first_seen
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TrackedItem':
        """Create from dictionary"""
        item = cls(data["name"], data["limit"])
        item.used_seconds = data.get("used", 0)
        item.daily_log = data.get("log", {})
        item.notified = data.get("notified", False)
        item.first_seen = data.get("first_seen", datetime.now().isoformat())
        return item
    
    def add_usage(self, seconds: int):
        """Add usage time"""
        if seconds > 0 and seconds < 60:  # Sanity check
            self.used_seconds += seconds
            today = datetime.now().strftime("%Y-%m-%d")
            self.daily_log[today] = self.daily_log.get(today, 0) + seconds
        
    def reset_daily(self):
        """Reset daily usage (can be called at midnight)"""
        self.used_seconds = 0
        self.notified = False
        
    @property
    def used_minutes(self) -> int:
        """Get used minutes"""
        return self.used_seconds // 60
    
    @property
    def limit_reached(self) -> bool:
        """Check if limit is reached"""
        return self.used_minutes >= self.limit_minutes