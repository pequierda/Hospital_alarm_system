#!/usr/bin/env python3
"""
Alarm System Client with GUI
Connects to server at 10.0.1.3 and displays alarm messages
Runs with GUI interface on workstations
"""

import socket
import json
import threading
import time
import sys
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import winsound
import pystray
from PIL import Image, ImageDraw, ImageTk
import io
import pygame
import base64

class AlarmClientGUI:
    def __init__(self, server_host='10.0.10.13', server_port=9999):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.running = False
        self.root = tk.Tk()
        self.tray_icon = None
        self.is_hidden = False
        
        # Initialize pygame mixer for audio
        try:
            pygame.mixer.init()
            self.audio_available = True
        except:
            self.audio_available = False
            print("Warning: Audio not available")
        
        self.setup_gui()
        self.setup_system_tray()
        
    def setup_gui(self):
        """Setup the main GUI window"""
        self.root.title("ACE MEDICAL CENTER PALAWAN")
        self.root.geometry("500x400")
        self.root.configure(bg='#2c3e50')
        
        # Configure window properties
        self.root.resizable(True, True)
        
        # Remove maximize and close buttons, keep only minimize
        self.root.attributes('-toolwindow', False)  # Keep normal window
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)  # Handle close attempt
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="HOSPITAL INCIDENT COMMAND SYSTEM", 
                              font=('Arial', 16, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=(0, 5))
        
        # Warning message
        warning_label = tk.Label(main_frame, text="⚠️ CLOSING WILL MINIMIZE TO SYSTEM TRAY ⚠️", 
                               font=('Arial', 10, 'bold'), 
                               fg='#f39c12', bg='#2c3e50')
        warning_label.pack(pady=(0, 10))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        self.status_label = tk.Label(status_frame, text="Disconnected", 
                                   font=('Arial', 12), 
                                   fg='#e74c3c', bg='#34495e')
        self.status_label.pack(pady=5)
        
        # Department info
        department_info = tk.Label(status_frame, text="HOSPITAL INCIDENT COMMAND SYSTEM", 
                                 font=('Arial', 10), 
                                 fg='#bdc3c7', bg='#34495e')
        department_info.pack()
        
        # No control buttons - client runs automatically
        
        # Log area
        log_frame = tk.Frame(main_frame, bg='#2c3e50')
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log title
        log_title = tk.Label(log_frame, text="HOSPITAL INCIDENT COMMAND SYSTEM Alarm Log", 
                            font=('Arial', 12, 'bold'), 
                            fg='white', bg='#2c3e50')
        log_title.pack(anchor=tk.W)
        
        # Scrolled text for logs
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 height=15, 
                                                 bg='#34495e', 
                                                 fg='white',
                                                 font=('Consolas', 9),
                                                 wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configure text tags for different message types
        self.log_text.tag_configure("fire", foreground="#e74c3c", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("security", foreground="#f39c12", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("test", foreground="#3498db", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("general", foreground="#2ecc71", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("info", foreground="#bdc3c7", font=('Consolas', 9))
        self.log_text.tag_configure("error", foreground="#e74c3c", font=('Consolas', 9, 'bold'))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        
        # Full-screen alarm window (initially hidden)
        self.alarm_window = None
        self.flicker_active = False
        self.flicker_job = None
        self.main_flicker_active = False
        self.main_flicker_job = None
        self.sound_looping = False
        
        # Start connection attempt
        self.root.after(1000, self.attempt_connection)
        
        # Start periodic reconnection attempts
        self.root.after(5000, self.periodic_reconnection_check)
        
    def attempt_connection(self):
        """Attempt to connect to server in background"""
        if not self.running:
            threading.Thread(target=self.connect_to_server, daemon=True).start()
    
    def periodic_reconnection_check(self):
        """Periodically check if we need to reconnect"""
        if not self.running:
            self.log_message("Attempting to reconnect to server...", "info")
            threading.Thread(target=self.connect_to_server, daemon=True).start()
        
        # Schedule next check in 10 seconds
        self.root.after(10000, self.periodic_reconnection_check)
    
    def connect_to_server(self):
        """Connect to the alarm server"""
        try:
            # Close existing socket if any
            self.close_socket()
            
            # Create new socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.server_host, self.server_port))
            self.running = True
            
            # Update GUI
            self.root.after(0, self.update_status, "Connected", "#27ae60")
            self.root.after(0, self.log_message, "Connected to alarm server", "info")
            
            # Start listening for alarms
            threading.Thread(target=self.listen_for_alarms, daemon=True).start()
            return True
        except Exception as e:
            error_msg = f"Failed to connect to server: {e}"
            self.root.after(0, self.log_message, error_msg, "error")
            self.root.after(0, self.update_status, "Disconnected", "#e74c3c")
            self.running = False
            self.close_socket()
            return False
    
    def update_status(self, status, color):
        """Update status label"""
        self.status_label.config(text=status, fg=color)
    
    def log_message(self, message, msg_type="info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%I:%M:%S %p")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.tag_add(msg_type, f"end-{len(log_entry.split(chr(10))[0])}c", "end-1c")
        self.log_text.see(tk.END)
    
    def listen_for_alarms(self):
        """Listen for alarm messages from server"""
        while self.running:
            try:
                data = self.socket.recv(1024)
                if not data:
                    self.root.after(0, self.log_message, "Server disconnected", "error")
                    self.root.after(0, self.update_status, "Disconnected", "#e74c3c")
                    self.running = False
                    self.close_socket()
                    break
                
                # Check if it's a ping message
                if data == b"ping":
                    continue
                
                # Parse alarm message
                try:
                    alarm_data = json.loads(data.decode('utf-8'))
                    self.root.after(0, self.handle_alarm, alarm_data)
                except json.JSONDecodeError:
                    self.root.after(0, self.log_message, f"Received invalid data: {data}", "error")
                    
            except socket.timeout:
                continue
            except Exception as e:
                self.root.after(0, self.log_message, f"Connection error: {e}", "error")
                self.root.after(0, self.update_status, "Disconnected", "#e74c3c")
                self.running = False
                self.close_socket()
                break
    
    def handle_alarm(self, alarm_data):
        """Handle incoming alarm message"""
        alarm_type = alarm_data.get('type', 'general')
        message = alarm_data.get('message', 'Unknown alarm')
        timestamp = alarm_data.get('timestamp', datetime.now().isoformat())
        
        # Get color information from alarm data
        color = alarm_data.get('color', '#e74c3c')
        bg_color = alarm_data.get('bg_color', '#8B0000')
        text_color = alarm_data.get('text_color', '#FFFFFF')
        icon = alarm_data.get('icon', '⚠️')
        name = alarm_data.get('name', 'Custom Alarm')
        background_image = alarm_data.get('background_image', None)
        
        # Convert timestamp to 12-hour format for log
        try:
            time_12hr = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%I:%M:%S %p")
        except:
            time_12hr = datetime.now().strftime("%I:%M:%S %p")
        
        # Log alarm to GUI
        self.log_message(f"ALARM RECEIVED: {message}", alarm_type)
        self.log_message(f"Color: {color} | Time: {time_12hr}", "info")
        if background_image:
            self.log_message(f"Background image received: {len(background_image)} bytes", "info")
        else:
            self.log_message("No background image in alarm", "info")
        
        # Show alarm popup with custom colors and background image
        self.show_alarm_popup(alarm_type, message, timestamp, color, bg_color, text_color, icon, name, background_image)
        
        # Play alarm sound
        self.play_alarm_sound(alarm_type)
    
    def show_alarm_popup(self, alarm_type, message, timestamp, color=None, bg_color=None, text_color=None, icon=None, name=None, background_image=None):
        """Show full-screen alarm display with flickering effect"""
        try:
            # Close existing alarm window if open
            if self.alarm_window:
                self.alarm_window.destroy()
            
            # Create full-screen alarm window
            self.alarm_window = tk.Toplevel(self.root)
            self.alarm_window.title("ALARM")
            self.alarm_window.configure(bg='#000000')
            
            # Make it full screen
            self.alarm_window.state('zoomed')  # Windows
            self.alarm_window.attributes('-fullscreen', True)  # Alternative for other systems
            
            # Remove window decorations
            self.alarm_window.overrideredirect(True)
            
            # Set window to topmost
            self.alarm_window.attributes('-topmost', True)
            
            # Store colors for flickering
            self.original_bg_color = bg_color
            self.original_text_color = text_color
            self.flicker_active = True
            
            # Use provided colors or defaults
            if not bg_color:
                bg_color = '#8B0000'
            if not text_color:
                text_color = '#FFFFFF'
            if not icon:
                icon = '⚠️'
            if not name:
                name = 'CUSTOM ALARM'
                
            title_text = f"{icon} {name.upper()} {icon}"
            
            # Configure window background
            self.alarm_window.configure(bg=bg_color)
            
            # Create main frame
            self.main_frame = tk.Frame(self.alarm_window, bg=bg_color)
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Handle background image if provided
            background_photo = None
            if background_image:
                try:
                    self.log_message("Processing background image...", "info")
                    # Decode base64 image data
                    image_bytes = base64.b64decode(background_image)
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    self.log_message(f"Image loaded: {pil_image.size[0]}x{pil_image.size[1]} pixels", "info")
                    
                    # Get screen dimensions for full-screen display
                    screen_width = self.alarm_window.winfo_screenwidth()
                    screen_height = self.alarm_window.winfo_screenheight()
                    
                    # Resize image to fit screen while maintaining aspect ratio
                    pil_image.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage for tkinter
                    background_photo = ImageTk.PhotoImage(pil_image)
                    
                    # Create a canvas to display the background image
                    self.background_canvas = tk.Canvas(self.main_frame, 
                                                     width=screen_width, 
                                                     height=screen_height,
                                                     highlightthickness=0)
                    self.background_canvas.pack(fill=tk.BOTH, expand=True)
                    
                    # Display the background image
                    self.background_canvas.create_image(screen_width//2, screen_height//2, 
                                                      image=background_photo, anchor=tk.CENTER)
                    self.log_message("Background image displayed on canvas", "info")
                    
                    # Create a minimal overlay for text visibility
                    # Use a very light overlay or no overlay at all
                    overlay = tk.Frame(self.background_canvas, bg='', highlightthickness=0)
                    self.background_canvas.create_window(screen_width//2, screen_height//2, 
                                                       window=overlay, anchor=tk.CENTER)
                    overlay.configure(width=screen_width, height=screen_height)
                    
                    # Use overlay as the main frame for content
                    self.content_frame = overlay
                    
                except Exception as e:
                    self.log_message(f"Error displaying background image: {e}", "error")
                    # Fallback to normal display without background image
                    self.content_frame = self.main_frame
            else:
                # No background image, use normal display
                self.content_frame = self.main_frame
            
            # Determine if we have a background image for styling
            has_background = background_image is not None
            
            # Large icon
            icon_bg = '' if has_background else bg_color
            self.icon_label = tk.Label(self.content_frame, text=icon, 
                                font=('Arial', 200, 'bold'), 
                                fg=text_color, bg=icon_bg)
            self.icon_label.pack(pady=(50, 20))
            
            # Title
            title_bg = '' if has_background else bg_color
            self.title_label = tk.Label(self.content_frame, text=title_text, 
                                 font=('Arial', 48, 'bold'), 
                                 fg=text_color, bg=title_bg)
            self.title_label.pack(pady=(0, 30))
            
            # Message
            message_bg = '' if has_background else bg_color
            self.message_label = tk.Label(self.content_frame, text=message, 
                                  font=('Arial', 24, 'bold'), 
                                  fg=text_color, bg=message_bg,
                                  wraplength=1000, justify=tk.CENTER)
            self.message_label.pack(pady=(0, 20))
            
            # Timestamp (convert to 12-hour format)
            time_12hr = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%I:%M:%S %p")
            time_bg = '' if has_background else bg_color
            self.time_label = tk.Label(self.content_frame, text=f"Time: {time_12hr}", 
                               font=('Arial', 18), 
                               fg=text_color, bg=time_bg)
            self.time_label.pack(pady=(0, 20))
            
            # Department info
            dept_bg = '' if has_background else bg_color
            self.department_label = tk.Label(self.content_frame, text="HOSPITAL INCIDENT COMMAND SYSTEM", 
                                     font=('Arial', 16), 
                                     fg=text_color, bg=dept_bg)
            self.department_label.pack(pady=(0, 50))
            
            # Close button
            self.close_btn = tk.Button(self.content_frame, text="CLOSE ALARM", 
                                command=self.close_alarm_window,
                                font=('Arial', 20, 'bold'),
                                bg=text_color, fg=bg_color,
                                relief=tk.RAISED, bd=5,
                                padx=20, pady=10)
            self.close_btn.pack(pady=(0, 50))
            
            # Start flickering effect
            self.start_flickering()
            
            # Also start flickering main window
            self.main_flicker_active = True
            self.start_main_window_flickering()
            
            # Auto-close after 30 seconds
            self.alarm_window.after(30000, self.auto_close_alarm)
            
        except Exception as e:
            self.log_message(f"Error showing full-screen alarm: {e}", "error")
    
    def start_flickering(self):
        """Start the flickering color effect"""
        if self.flicker_active and self.alarm_window:
            # Alternate between original colors and bright white/red
            flicker_bg = '#FFFFFF' if self.original_bg_color != '#FFFFFF' else '#FF0000'
            flicker_text = '#000000' if self.original_text_color != '#000000' else '#FFFFFF'
            
            # Apply flickering colors
            self.alarm_window.configure(bg=flicker_bg)
            self.main_frame.configure(bg=flicker_bg)
            if hasattr(self, 'content_frame'):
                self.content_frame.configure(bg=flicker_bg)
            self.icon_label.configure(bg=flicker_bg, fg=flicker_text)
            self.title_label.configure(bg=flicker_bg, fg=flicker_text)
            self.message_label.configure(bg=flicker_bg, fg=flicker_text)
            self.time_label.configure(bg=flicker_bg, fg=flicker_text)
            self.department_label.configure(bg=flicker_bg, fg=flicker_text)
            self.close_btn.configure(bg=flicker_text, fg=flicker_bg)
            
            # Schedule next flicker (alternate every 500ms)
            self.flicker_job = self.alarm_window.after(500, self.flicker_to_original)
    
    def flicker_to_original(self):
        """Flicker back to original colors"""
        if self.flicker_active and self.alarm_window:
            # Apply original colors
            self.alarm_window.configure(bg=self.original_bg_color)
            self.main_frame.configure(bg=self.original_bg_color)
            if hasattr(self, 'content_frame'):
                self.content_frame.configure(bg=self.original_bg_color)
            self.icon_label.configure(bg=self.original_bg_color, fg=self.original_text_color)
            self.title_label.configure(bg=self.original_bg_color, fg=self.original_text_color)
            self.message_label.configure(bg=self.original_bg_color, fg=self.original_text_color)
            self.time_label.configure(bg=self.original_bg_color, fg=self.original_text_color)
            self.department_label.configure(bg=self.original_bg_color, fg=self.original_text_color)
            self.close_btn.configure(bg=self.original_text_color, fg=self.original_bg_color)
            
            # Schedule next flicker
            self.flicker_job = self.alarm_window.after(500, self.start_flickering)
    
    def start_main_window_flickering(self):
        """Start flickering the main client window"""
        if self.main_flicker_active:
            # Alternate between original and red background
            current_bg = self.root.cget('bg')
            if current_bg == '#2c3e50':
                self.root.configure(bg='#e74c3c')
            else:
                self.root.configure(bg='#2c3e50')
            
            # Schedule next flicker
            self.main_flicker_job = self.root.after(300, self.start_main_window_flickering)
    
    def stop_main_window_flickering(self):
        """Stop flickering the main client window"""
        self.main_flicker_active = False
        if self.main_flicker_job:
            self.root.after_cancel(self.main_flicker_job)
            self.main_flicker_job = None
        # Restore original background
        self.root.configure(bg='#2c3e50')
    
    def auto_close_alarm(self):
        """Auto-close alarm after 30 seconds"""
        self.log_message("Alarm auto-closed after 30 seconds", "info")
        self.close_alarm_window()
    
    def close_alarm_window(self):
        """Close the full-screen alarm window"""
        # Stop flickering effects
        self.flicker_active = False
        if self.flicker_job:
            self.alarm_window.after_cancel(self.flicker_job)
            self.flicker_job = None
        
        # Stop main window flickering
        self.stop_main_window_flickering()
        
        # Stop looping alarm sound
        self.stop_alarm_sound()
        
        if self.alarm_window:
            self.alarm_window.destroy()
            self.alarm_window = None
    
    def play_alarm_sound(self, alarm_type):
        """Play alarm sound using alarm.mp3 with looping"""
        try:
            if self.audio_available:
                # Try to play alarm.mp3 file with looping
                alarm_file = "alarm.mp3"
                if os.path.exists(alarm_file):
                    pygame.mixer.music.load(alarm_file)
                    pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                    self.sound_looping = True
                    self.log_message(f"Playing looping alarm sound: {alarm_file}", "info")
                else:
                    # Fallback to system beep if alarm.mp3 not found
                    self.log_message(f"alarm.mp3 not found, using system beep", "warning")
                    winsound.Beep(1000, 1000)
            else:
                # Fallback to system beep if pygame not available
                winsound.Beep(1000, 1000)
        except Exception as e:
            self.log_message(f"Error playing sound: {e}", "error")
            # Final fallback to system beep
            try:
                winsound.Beep(1000, 1000)
            except:
                pass
    
    def stop_alarm_sound(self):
        """Stop the looping alarm sound"""
        try:
            if self.audio_available and self.sound_looping:
                pygame.mixer.music.stop()
                self.sound_looping = False
                self.log_message("Stopped alarm sound", "info")
        except Exception as e:
            self.log_message(f"Error stopping sound: {e}", "error")
    
    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        self.close_socket()
        self.update_status("Disconnected", "#e74c3c")
        self.log_message("Disconnected from alarm server", "info")
    
    def close_socket(self):
        """Close socket connection safely"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
    
    def create_tray_icon(self):
        """Create a simple icon for the system tray"""
        # Create a simple icon image
        width = height = 64
        image = Image.new('RGB', (width, height), color='#2c3e50')
        dc = ImageDraw.Draw(image)
        
        # Draw a simple alarm bell icon
        dc.ellipse([16, 16, 48, 48], fill='#e74c3c', outline='white', width=2)
        dc.text((20, 25), 'A', fill='white')
        
        return image
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        try:
            icon_image = self.create_tray_icon()
            
            menu = pystray.Menu(
                pystray.MenuItem("Show HOSPITAL INCIDENT COMMAND SYSTEM Client", self.show_window),
                pystray.MenuItem("Exit", self.quit_application)
            )
            
            self.tray_icon = pystray.Icon(
                "HOSPITAL INCIDENT COMMAND SYSTEM Client",
                icon_image,
                "HOSPITAL INCIDENT COMMAND SYSTEM",
                menu
            )
            
            # Start tray icon in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            self.log_message(f"Error setting up system tray: {e}", "error")
    
    def hide_to_tray(self):
        """Hide window to system tray"""
        self.is_hidden = True
        self.root.withdraw()  # Hide the window
        self.log_message("Window minimized to system tray", "info")
    
    def show_window(self, icon=None, item=None):
        """Show the main window from system tray"""
        self.is_hidden = False
        self.root.deiconify()  # Show the window
        self.root.lift()  # Bring to front
        self.root.focus_force()  # Focus the window
        self.log_message("Window restored from system tray", "info")
    
    def quit_application(self, icon=None, item=None):
        """Quit the application completely"""
        self.disconnect()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
    
    def on_closing(self):
        """Handle window close event"""
        self.disconnect()
        self.root.destroy()
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main function to run the alarm client with GUI"""
    try:
        client = AlarmClientGUI()
        client.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
