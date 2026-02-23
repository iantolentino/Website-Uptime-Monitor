import json
from typing import Dict
from pathlib import Path
from models.tracked_item import TrackedItem
from config.settings import DATA_FILE


class DataManager:
    """Manages data persistence"""
    
    def __init__(self):
        self.data_file = DATA_FILE
        self.items: Dict[str, TrackedItem] = {}
        self.load_data()
        
    def load_data(self):
        """Load tracked items from file"""
        if Path(self.data_file).exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for name, item_data in data.items():
                        self.items[name] = TrackedItem.from_dict(item_data)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading data: {e}")
                self.items = {}
        else:
            self.items = {}
            
    def save_data(self):
        """Save tracked items to file"""
        data = {name: item.to_dict() for name, item in self.items.items()}
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving data: {e}")
            
    def add_item(self, name: str, limit: int):
        """Add new tracked item"""
        self.items[name.lower()] = TrackedItem(name, limit)
        self.save_data()
        
    def remove_item(self, name: str):
        """Remove tracked item"""
        if name in self.items:
            del self.items[name]
            self.save_data()
            
    def update_item(self, name: str, limit: int):
        """Update tracked item limit"""
        if name in self.items:
            self.items[name].limit_minutes = limit
            self.items[name].notified = False
            self.save_data()
            
    def get_all_items(self):
        """Get all tracked items"""
        return self.items