#!/usr/bin/env python3
"""
Debug launcher for Alarm Server
This script runs the server with full error output to diagnose issues
"""

import sys
import os

def main():
    """Run the alarm server GUI with debug output"""
    try:
        print("=== ALARM SERVER DEBUG LAUNCHER ===")
        print("Starting Alarm Server GUI with debug output...")
        print()
        
        # Check if alarm_server_gui.py exists
        if not os.path.exists("alarm_server_gui.py"):
            print("ERROR: alarm_server_gui.py not found!")
            print("Make sure you're running this from the correct directory.")
            input("Press Enter to exit...")
            return
        
        # Check Python version
        print(f"Python version: {sys.version}")
        print(f"Python executable: {sys.executable}")
        print()
        
        # Check required modules
        print("Checking required modules...")
        try:
            import tkinter
            print("✓ tkinter available")
        except ImportError as e:
            print(f"✗ tkinter not available: {e}")
            return
            
        try:
            import PIL
            print("✓ PIL (Pillow) available")
        except ImportError as e:
            print(f"✗ PIL not available: {e}")
            print("Install with: pip install Pillow")
            
        try:
            import pystray
            print("✓ pystray available")
        except ImportError as e:
            print(f"✗ pystray not available: {e}")
            print("Install with: pip install pystray")
            
        print()
        
        # Import and run the server directly
        print("Loading alarm_server_gui module...")
        try:
            import alarm_server_gui
            print("✓ Module loaded successfully")
        except Exception as e:
            print(f"✗ Module load failed: {e}")
            import traceback
            traceback.print_exc()
            input("Press Enter to exit...")
            return
        
        print()
        print("Starting GUI...")
        print("If the GUI doesn't appear, check for error messages below.")
        print("=" * 50)
        
        # Run the server
        alarm_server_gui.main()
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
