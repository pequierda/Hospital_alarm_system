#!/usr/bin/env python3
"""
Simple GUI launcher for Alarm Server
This script runs the server GUI directly without subprocess complications
"""

import sys
import os

def main():
    """Run the alarm server GUI directly"""
    try:
        print("Starting Alarm Server GUI...")
        
        # Check if alarm_server_gui.py exists
        if not os.path.exists("alarm_server_gui.py"):
            print("ERROR: alarm_server_gui.py not found!")
            print("Make sure you're running this from the correct directory.")
            input("Press Enter to exit...")
            return
        
        # Import and run the server directly
        print("Loading alarm server...")
        import alarm_server_gui
        
        print("Starting GUI...")
        alarm_server_gui.main()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install tkinter pillow pystray")
        input("Press Enter to exit...")
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
