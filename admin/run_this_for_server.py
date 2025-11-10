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
        
        # Check if alarm_server_gui.py exists
        if not os.path.exists("alarm_server_gui.py"):
            print("ERROR: alarm_server_gui.py not found!")
            print("Make sure you're running this from the correct directory.")
            input("Press Enter to exit...")
            return
        
        print(f"Using Python executable: {python_exe}")
        print("Launching alarm server GUI...")
        
        # Launch the server as a detached process
        try:
            if os.name == 'nt':  # Windows
                # Don't use DETACHED_PROCESS to see GUI immediately
                process = subprocess.Popen([python_exe, "alarm_server_gui.py"])
            else:  # Unix-like systems
                process = subprocess.Popen([python_exe, "alarm_server_gui.py"], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL,
                                       start_new_session=True)
            
            print("Server process started successfully!")
            print("The server GUI should open shortly.")
            print("If the GUI doesn't appear, check the system tray.")
            print("You can close this window - the server will continue running.")
            print("To stop the server, right-click the tray icon and select 'Exit'.")
            print()
            
            # Give the GUI time to start
            time.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                print("✓ Server process is running")
            else:
                print("✗ Server process exited unexpectedly")
                print("This might indicate an error in the server startup")
                
        except Exception as launch_error:
            print(f"Error launching server: {launch_error}")
            print("Trying alternative method...")
            
            # Fallback: try running directly
            try:
                import alarm_server_gui
                print("Starting server directly...")
                alarm_server_gui.main()
            except Exception as direct_error:
                print(f"Direct execution failed: {direct_error}")
                raise launch_error
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
