#!/usr/bin/env python3
"""
Application Usage Monitor
Tracks time spent on applications/websites with session management
"""

import sys
from utils.data_manager import DataManager
from core.monitor import UsageMonitor
from ui.main_window import MainWindow


def main():
    """Main application entry point"""
    try:
        # Initialize data manager
        data_manager = DataManager()
        
        # Initialize monitor with UI update callback
        monitor = UsageMonitor(data_manager)
        
        # Initialize and run UI
        app = MainWindow(data_manager, monitor)
        
        # Start monitoring
        monitor.start()
        
        # Run the application
        app.run()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        if 'monitor' in locals():
            monitor.stop()
        if 'data_manager' in locals():
            data_manager.save_data()
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()