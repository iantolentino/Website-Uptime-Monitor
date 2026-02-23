import time
import threading
import psutil
from typing import Callable, Optional, Tuple
import pywinctl
from core.session import SessionManager
from models.tracked_item import TrackedItem
from config.settings import MONITOR_INTERVAL
import os
import sys


class UsageMonitor:
    """Monitors active window usage with power efficiency"""
    
    def __init__(self, data_manager, update_callback: Optional[Callable] = None):
        self.data_manager = data_manager
        self.session_manager = SessionManager()
        self.update_callback = update_callback
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_check_time = time.time()
        self.current_app = None
        self.current_app_pid = None
        self.app_cache = {}  # Cache for app names to reduce system calls
        
    def start(self):
        """Start monitoring in background thread"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("✓ Monitoring started - tracking all open applications")
        print("  Detected apps will appear automatically in the list")
        
    def stop(self):
        """Stop monitoring"""
        self.running = False
        self.session_manager.shutdown()
        
    def _get_window_process_name(self, hwnd) -> Tuple[Optional[str], Optional[int]]:
        """Get process name from window handle"""
        try:
            if sys.platform == "win32":
                import win32process
                import win32gui
                
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    return process.name().replace('.exe', '').lower(), pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return None, pid
            else:
                # For Linux/Mac - simplified version
                return None, None
        except Exception as e:
            # Fallback method
            return None, None
            
    def _get_active_app_info(self) -> Tuple[Optional[str], Optional[int]]:
        """Get active application name and PID"""
        try:
            active_window = pywinctl.getActiveWindow()
            
            if not active_window:
                return None, None
                
            app_name = None
            pid = None
            
            # Try multiple methods to get the app name
            
            # Method 1: Get from window handle (most accurate)
            if hasattr(active_window, 'handle'):
                app_name, pid = self._get_window_process_name(active_window.handle)
                
            # Method 2: Get from window title (fallback)
            if not app_name and active_window.title:
                title = active_window.title.lower()
                
                # Common patterns in window titles
                # Often it's "Filename - AppName" or "AppName"
                parts = title.split(' - ')
                if len(parts) > 1:
                    # Usually the last part is the app name
                    potential_app = parts[-1].strip()
                    if len(potential_app) > 1 and not potential_app.startswith(('http', 'www')):
                        app_name = potential_app
                else:
                    # Just use the first part of the title
                    app_name = parts[0][:30]  # Truncate long titles
                    
            # Method 3: Get from process list by window title (another fallback)
            if not app_name and active_window.title:
                app_name = self._guess_app_from_processes(active_window.title)
                
            # Clean up the app name
            if app_name:
                # Remove common suffixes
                app_name = app_name.replace('.exe', '').replace('.app', '')
                # Limit length
                app_name = app_name[:50]
                
            return app_name, pid
            
        except Exception as e:
            print(f"Debug - Error getting active app: {e}")
            return None, None
            
    def _guess_app_from_processes(self, window_title: str) -> Optional[str]:
        """Try to guess which app a window belongs to by looking at running processes"""
        try:
            # Common mappings of process names to display names
            common_mappings = {
                'chrome': 'google chrome',
                'firefox': 'firefox',
                'msedge': 'microsoft edge',
                'winword': 'microsoft word',
                'excel': 'microsoft excel',
                'powerpnt': 'microsoft powerpoint',
                'outlook': 'microsoft outlook',
                'slack': 'slack',
                'discord': 'discord',
                'spotify': 'spotify',
                'code': 'visual studio code',
                'pycharm64': 'pycharm',
                'intellij': 'intellij idea',
                'terminal': 'terminal',
                'cmd': 'command prompt',
                'explorer': 'file explorer',
                'notepad': 'notepad',
                'calculator': 'calculator',
            }
            
            # Get top CPU/memory using processes that might be the active app
            processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_name = proc.info['name'].lower()
                    # Filter out system processes
                    if proc_name and len(proc_name) > 2 and not proc_name.startswith(('svchost', 'system')):
                        # Check if this process name is in the window title
                        if proc_name.replace('.exe', '') in window_title.lower():
                            return common_mappings.get(proc_name, proc_name.replace('.exe', ''))
                except:
                    pass
                    
            return None
        except:
            return None
            
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_save_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                elapsed = current_time - self.last_check_time
                
                # Don't count time if elapsed is too large (computer woke from sleep)
                if elapsed > 5:
                    elapsed = 1
                    
                # Get current active application
                app_name, pid = self._get_active_app_info()
                
                if app_name and app_name != 'system' and len(app_name) > 1:
                    # Update session
                    self.session_manager.update_activity(app_name)
                    
                    # Track current app
                    self.current_app = app_name
                    self.current_app_pid = pid
                    
                    # Debug output (remove in production)
                    if int(current_time) % 10 == 0:  # Print every 10 seconds
                        print(f"Debug - Active app: {app_name}")
                    
                    # Update usage for ALL tracked items
                    items = self.data_manager.get_all_items()
                    updated = False
                    
                    for item_name, item in items.items():
                        # Check if this tracked item matches the active app
                        # More flexible matching
                        if (item_name in app_name or 
                            app_name in item_name or
                            self._fuzzy_match(item_name, app_name)):
                            
                            item.add_usage(int(elapsed))
                            item.is_active = True
                            item.last_active_time = current_time
                            updated = True
                            
                            # Check for limit notification
                            if item.limit_reached and not item.notified:
                                self._send_notification(item)
                                item.notified = True
                        else:
                            # Check if app was recently active
                            if (item.last_active_time and 
                                current_time - item.last_active_time > 60):
                                item.is_active = False
                    
                    # Auto-detect new applications
                    self._auto_detect_app(app_name)
                    
                    # Save data periodically (every 30 seconds)
                    if current_time - last_save_time > 30:
                        self.data_manager.save_data()
                        last_save_time = current_time
                        
                # Check for idle
                self.session_manager.check_idle()
                
                # Trigger UI update
                if self.update_callback and int(current_time) % 2 == 0:
                    self.update_callback()
                    
                self.last_check_time = current_time
                
            except Exception as e:
                print(f"Monitor error: {e}")
                import traceback
                traceback.print_exc()
                
            # Sleep efficiently
            time.sleep(MONITOR_INTERVAL)
            
    def _fuzzy_match(self, tracked_name: str, app_name: str) -> bool:
        """Fuzzy match app names"""
        tracked_name = tracked_name.lower()
        app_name = app_name.lower()
        
        # Direct match
        if tracked_name == app_name:
            return True
            
        # One is substring of the other
        if tracked_name in app_name or app_name in tracked_name:
            return True
            
        # Common variations
        variations = {
            'chrome': ['google chrome', 'chrome'],
            'word': ['microsoft word', 'winword', 'word'],
            'excel': ['microsoft excel', 'excel'],
            'powerpoint': ['microsoft powerpoint', 'powerpnt', 'powerpoint'],
            'outlook': ['microsoft outlook', 'outlook'],
            'vscode': ['visual studio code', 'code', 'vscode'],
            'pycharm': ['pycharm', 'jetbrains pycharm'],
            'terminal': ['terminal', 'cmd', 'command prompt', 'powershell'],
        }
        
        for key, variants in variations.items():
            if (tracked_name in variants and app_name in variants) or \
               (app_name in variants and tracked_name in variants):
                return True
                
        return False
            
    def _auto_detect_app(self, app_name: str):
        """Automatically detect and add new applications"""
        try:
            items = self.data_manager.get_all_items()
            
            # Don't auto-add if it's already tracked
            if app_name in items:
                return
                
            # Check if this is a real application (not a system window)
            skip_patterns = [
                'program manager', 'system', 'settings', 'start',
                'task switching', 'window', 'desktop', 'screen'
            ]
            
            if any(pattern in app_name.lower() for pattern in skip_patterns):
                return
                
            # Auto-add with default 60 minute limit
            if len(app_name) > 2 and app_name not in items:
                print(f"📱 Auto-detected new app: {app_name}")
                # Uncomment to enable auto-add:
                # self.data_manager.add_item(app_name, 60)
                
        except Exception as e:
            print(f"Auto-detect error: {e}")
            
    def _send_notification(self, item: TrackedItem):
        """Send limit reached notification"""
        try:
            from plyer import notification
            notification.notify(
                title="⏰ Time Limit Reached",
                message=f"You've used {item.name} for {item.limit_minutes} minutes.",
                timeout=5
            )
        except:
            print(f"🔔 Time limit: {item.name} - {item.limit_minutes} minutes")

    

    def debug_windows(self):
        """Debug function to see all windows"""
        try:
            windows = pywinctl.getAllWindows()
            print(f"\n=== All Windows ({len(windows)}) ===")
            for i, win in enumerate(windows[:10]):  # Show first 10
                if win.title:
                    print(f"{i+1}. Title: {win.title}")
            print("=" * 30)
        except:
            pass