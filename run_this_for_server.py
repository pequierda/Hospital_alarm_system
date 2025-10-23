#!/usr/bin/env python3
"""
Independent runner for Alarm Server
This script runs the server independently, allowing the console to be closed
"""

import sys
import os
import subprocess
import time

def main():
    """Run the alarm server independently"""
    try:
        print("Starting Alarm Server...")
        print("The server will run in the system tray.")
        print("You can close this window after the server starts.")
        print()
        
        # Use pythonw.exe to run the server without a console window
        # This ensures the server runs independently of this console
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        
        # Fallback to python.exe if pythonw.exe doesn't exist
        if not os.path.exists(python_exe):
            python_exe = sys.executable
        
        # Launch the server as a detached process
        if os.name == 'nt':  # Windows
            # Use DETACHED_PROCESS to run independently of console
            subprocess.Popen([python_exe, "alarm_server_gui.py"], 
                           creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
        else:  # Unix-like systems
            subprocess.Popen([python_exe, "alarm_server_gui.py"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
        
        print("Server started successfully!")
        print("The server is now running in the system tray.")
        print("You can close this window - the server will continue running.")
        print("To stop the server, right-click the tray icon and select 'Exit'.")
        print()
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
