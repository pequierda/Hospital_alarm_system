#!/usr/bin/env python3
"""
Alarm System Server with GUI
Runs on 10.0.1.3 and broadcasts alarm messages to connected clients
Features a modern GUI interface for easy alarm management
"""

import socket
import threading
import time
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext, colorchooser
import pystray
from PIL import Image, ImageDraw
import sys
import hashlib
import os
import secrets
import string

class AlarmServerGUI:
    def __init__(self, host='10.0.10.13', port=9999):
        self.host = host
        self.port = port
        self.clients = []
        self.running = False
        self.socket = None
        self.root = tk.Tk()
        self.tray_icon = None
        self.is_hidden = False
        
        # Selected alarm type for instructions
        self.selected_alarm_type = None
        self.with_instructions = tk.BooleanVar()
        
        # Selected color for alarms
        self.selected_color = '#e74c3c'  # Default red color
        
        
        # Admin authentication
        self.password_file = "admin_password.txt"
        self.current_admin = None
        self.is_authenticated = False
        self.admin_password = self.load_admin_password()
        
        # Floor selection
        self.floors = [
            'B2', 'B1', 'Ground Floor', '2nd Floor', '3rd Floor', 
            '4th Floor', '5th Floor', '6th Floor', '7th Floor', '8th Floor'
        ]
        self.selected_floor = 'Ground Floor'  # Default floor
        
        # SECURITY: Check if password file exists before starting
        if not os.path.exists(self.password_file):
            self.log_message("SECURITY ALERT: Admin password file missing!", "error")
            self.log_message("Server cannot start without password file", "error")
            messagebox.showerror("Security Alert", 
                               "Admin password file is missing!\n\n"
                               "This could indicate unauthorized access.\n"
                               "Please contact your system administrator.\n\n"
                               "Use password_manager.py to reset the password.")
            sys.exit(1)
        
        self.setup_gui()
        # Setup system tray after GUI is ready
        self.root.after(2000, self.setup_system_tray)
    
    def hash_password(self, password):
        """Hash a password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password, stored_hash):
        """Verify a password against stored hash"""
        try:
            salt, password_hash = stored_hash.split(':')
            test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return test_hash == password_hash
        except:
            return False
    
    def load_admin_password(self):
        """Load admin password from file or create default"""
        try:
            if os.path.exists(self.password_file):
                with open(self.password_file, 'r') as f:
                    return f.read().strip()
            else:
                # SECURITY: Don't auto-generate password if file is missing
                # This prevents unauthorized access if file is deleted
                self.log_message("SECURITY ALERT: Admin password file is missing!", "error")
                self.log_message("Server will not start until password is set manually", "error")
                self.log_message("Use password_manager.py to set a new password", "error")
                raise FileNotFoundError("Admin password file missing - manual intervention required")
        except Exception as e:
            self.log_message(f"Error loading password: {e}", "error")
            raise Exception("Cannot start server without valid password file")
    
    def generate_secure_password(self, length=12):
        """Generate a secure random password"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password
    
    def save_admin_password(self, hashed_password):
        """Save hashed password to file"""
        try:
            with open(self.password_file, 'w') as f:
                f.write(hashed_password)
            return True
        except Exception as e:
            self.log_message(f"Error saving password: {e}", "error")
            return False
        
    def setup_gui(self):
        """Setup the main GUI window"""
        self.root.title("ACE MEDICAL CENTER PALAWAN")
        self.root.geometry("700x600")
        self.root.configure(bg='#2c3e50')
        
        # Make window resizable
        self.root.resizable(True, True)
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="HOSPITAL INCIDENT COMMAND SYSTEM", 
                              font=('Arial', 18, 'bold'), 
                              fg='white', bg='#2c3e50')
        title_label.pack(pady=(0, 10))
        
        # Server status frame
        status_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status and controls
        status_controls = tk.Frame(status_frame, bg='#34495e')
        status_controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Server status
        self.status_label = tk.Label(status_controls, text="Server Stopped", 
                                   font=('Arial', 14, 'bold'), 
                                   fg='#e74c3c', bg='#34495e')
        self.status_label.pack(side=tk.LEFT)
        
        # Start/Stop button
        self.start_btn = tk.Button(status_controls, text="Start Server", 
                                 command=self.toggle_server,
                                 bg='#27ae60', fg='white', 
                                 font=('Arial', 12, 'bold'),
                                 relief=tk.RAISED, bd=3)
        self.start_btn.pack(side=tk.RIGHT)
        
        # Server info
        server_info = tk.Label(status_frame, text=f"Host: {self.host} | Port: {self.port}", 
                              font=('Arial', 10), 
                              fg='#bdc3c7', bg='#34495e')
        server_info.pack(pady=(0, 5))
        
        # Tray warning
        tray_warning = tk.Label(status_frame, text="⚠️ Closing window will minimize to system tray ⚠️", 
                               font=('Arial', 9, 'bold'), 
                               fg='#f39c12', bg='#34495e')
        tray_warning.pack(pady=(0, 5))
        
        # Tray status
        self.tray_status_label = tk.Label(status_frame, text="System Tray: Initializing...", 
                                         font=('Arial', 9), 
                                         fg='#bdc3c7', bg='#34495e')
        self.tray_status_label.pack(pady=(0, 10))
        
        # Admin authentication frame
        admin_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        admin_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Admin title
        admin_title = tk.Label(admin_frame, text="Admin Authentication", 
                              font=('Arial', 12, 'bold'), 
                              fg='white', bg='#34495e')
        admin_title.pack(pady=(10, 5))
        
        # Admin controls
        admin_controls = tk.Frame(admin_frame, bg='#34495e')
        admin_controls.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Admin name field
        admin_name_frame = tk.Frame(admin_controls, bg='#34495e')
        admin_name_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(admin_name_frame, text="Admin Name:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#34495e').pack(side=tk.LEFT)
        
        self.admin_name_entry = tk.Entry(admin_name_frame, font=('Arial', 10), width=20)
        self.admin_name_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Admin password field
        admin_pass_frame = tk.Frame(admin_controls, bg='#34495e')
        admin_pass_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(admin_pass_frame, text="Password:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#34495e').pack(side=tk.LEFT)
        
        self.admin_pass_entry = tk.Entry(admin_pass_frame, font=('Arial', 10), width=20, show="*")
        self.admin_pass_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Login button
        self.login_btn = tk.Button(admin_pass_frame, text="Login", 
                                 command=self.authenticate_admin,
                                 bg='#27ae60', fg='white', 
                                 font=('Arial', 10, 'bold'))
        self.login_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Logout button
        self.logout_btn = tk.Button(admin_pass_frame, text="Logout", 
                                  command=self.logout_admin,
                                  bg='#e74c3c', fg='white', 
                                  font=('Arial', 10, 'bold'),
                                  state=tk.DISABLED)
        self.logout_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Change password button
        self.change_password_btn = tk.Button(admin_pass_frame, text="Change Password", 
                                           command=self.show_change_password_dialog,
                                           bg='#9b59b6', fg='white', 
                                           font=('Arial', 10, 'bold'),
                                           state=tk.DISABLED)
        self.change_password_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Admin status
        self.admin_status_label = tk.Label(admin_controls, text="Not Authenticated", 
                                         font=('Arial', 10, 'bold'), 
                                         fg='#e74c3c', bg='#34495e')
        self.admin_status_label.pack(pady=(5, 0))
        
        # Connected clients frame
        clients_frame = tk.Frame(main_frame, bg='#2c3e50')
        clients_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Clients title
        clients_title = tk.Label(clients_frame, text="Connected Clients", 
                               font=('Arial', 12, 'bold'), 
                               fg='white', bg='#2c3e50')
        clients_title.pack(anchor=tk.W)
        
        # Clients listbox
        clients_list_frame = tk.Frame(clients_frame, bg='#34495e', relief=tk.SUNKEN, bd=1)
        clients_list_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.clients_listbox = tk.Listbox(clients_list_frame, height=4, 
                                         bg='#34495e', fg='white',
                                         font=('Consolas', 9),
                                         selectbackground='#3498db')
        self.clients_listbox.pack(fill=tk.X, padx=5, pady=5)
        
        # Alarm controls frame
        alarm_frame = tk.Frame(main_frame, bg='#2c3e50')
        alarm_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Alarm title
        alarm_title = tk.Label(alarm_frame, text="Send Alarm", 
                             font=('Arial', 12, 'bold'), 
                             fg='white', bg='#2c3e50')
        alarm_title.pack(anchor=tk.W)
        
        # Alarm controls
        controls_frame = tk.Frame(alarm_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        controls_frame.pack(fill=tk.X, pady=(5, 0))
        
        
        # Color selection frame
        color_frame = tk.Frame(controls_frame, bg='#34495e')
        color_frame.pack(fill=tk.X, padx=10, pady=(5, 5))
        
        tk.Label(color_frame, text="Alarm Color:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#34495e').pack(side=tk.LEFT)
        
        # Color preview
        self.color_preview = tk.Frame(color_frame, width=40, height=30, bg=self.selected_color, relief=tk.SUNKEN, bd=2)
        self.color_preview.pack(side=tk.LEFT, padx=(10, 0))
        
        # Color picker button
        self.color_picker_btn = tk.Button(color_frame, text="Choose Color", 
                                        command=self.choose_color,
                                        bg='#9b59b6', fg='white', 
                                        font=('Arial', 10, 'bold'))
        self.color_picker_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        
        # Custom message frame
        custom_frame = tk.Frame(controls_frame, bg='#34495e')
        custom_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Custom message entry (without label)
        entry_frame = tk.Frame(custom_frame, bg='#34495e')
        entry_frame.pack(fill=tk.X)
        
        self.message_entry = tk.Entry(entry_frame, font=('Arial', 10), width=40)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.send_btn = tk.Button(entry_frame, text="Send", 
                                command=self.send_custom_alarm,
                                bg='#3498db', fg='white', 
                                font=('Arial', 10, 'bold'))
        self.send_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Quick alarm buttons
        quick_frame = tk.Frame(controls_frame, bg='#34495e')
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(quick_frame, text="Quick Alarms:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#34495e').pack(anchor=tk.W)
        
        # Floor selection frame
        floor_frame = tk.Frame(quick_frame, bg='#34495e')
        floor_frame.pack(fill=tk.X, padx=0, pady=(5, 5))
        
        tk.Label(floor_frame, text="Select Floor:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#34495e').pack(side=tk.LEFT)
        
        # Floor selection combobox
        self.floor_var = tk.StringVar(value=self.selected_floor)
        self.floor_combo = ttk.Combobox(floor_frame, textvariable=self.floor_var, 
                                       values=self.floors, 
                                       state='readonly', width=15)
        self.floor_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.floor_combo.bind('<<ComboboxSelected>>', self.on_floor_changed)
        
        # Quick alarm buttons
        buttons_frame = tk.Frame(quick_frame, bg='#34495e')
        buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Floor info for quick alarms
        floor_info_frame = tk.Frame(buttons_frame, bg='#34495e')
        floor_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(floor_info_frame, text="floor threat alarms on:", 
                font=('Arial', 9), 
                fg='#bdc3c7', bg='#34495e').pack(side=tk.LEFT)
        
        self.floor_display = tk.Label(floor_info_frame, text=self.selected_floor, 
                                     font=('Arial', 9, 'bold'), 
                                     fg='#f39c12', bg='#34495e')
        self.floor_display.pack(side=tk.LEFT, padx=(5, 0))
        
        # FIRE RESPONSE - RED
        self.fire_btn = tk.Button(buttons_frame, text="🔥 FIRE RESPONSE - RED", 
                                command=self.send_fire_alarm,
                                bg='#e74c3c', fg='white', 
                                font=('Arial', 9, 'bold'),
                                relief=tk.RAISED, bd=2)
        self.fire_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # MISSING CHILD / ABDUCTED - AMBER
        self.missing_child_btn = tk.Button(buttons_frame, text="👶 MISSING CHILD / ABDUCTED - AMBER", 
                                         command=self.send_missing_child_alarm,
                                    bg='#f39c12', fg='white', 
                                         font=('Arial', 9, 'bold'),
                                    relief=tk.RAISED, bd=2)
        self.missing_child_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add more buttons in a second row
        buttons_frame2 = tk.Frame(quick_frame, bg='#34495e')
        buttons_frame2.pack(fill=tk.X, pady=(5, 0))
        
        # MISSING ADULT PATIENT - YELLOW
        self.missing_adult_btn = tk.Button(buttons_frame2, text="👤 MISSING ADULT PATIENT - YELLOW", 
                                          command=self.send_missing_adult_alarm,
                                          bg='#f1c40f', fg='black', 
                                          font=('Arial', 9, 'bold'),
                                relief=tk.RAISED, bd=2)
        self.missing_adult_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # BOMB THREAT - BLACK
        self.bomb_threat_btn = tk.Button(buttons_frame2, text="💣 BOMB THREAT - BLACK", 
                                        command=self.send_bomb_threat_alarm,
                                        bg='#2c3e50', fg='white', 
                                        font=('Arial', 9, 'bold'),
                                     relief=tk.RAISED, bd=2)
        self.bomb_threat_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add more buttons in a third row
        buttons_frame3 = tk.Frame(quick_frame, bg='#34495e')
        buttons_frame3.pack(fill=tk.X, pady=(5, 0))
        
        # VIOLENT SITUATION - GRAY
        self.violent_situation_btn = tk.Button(buttons_frame3, text="⚔️ VIOLENT SITUATION - GRAY", 
                                              command=self.send_violent_situation_alarm,
                                              bg='#95a5a6', fg='white', 
                                              font=('Arial', 9, 'bold'),
                                      relief=tk.RAISED, bd=2)
        self.violent_situation_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # ACTIVE SHOOTER / ARMED INTRUDER - SILVER
        self.active_shooter_btn = tk.Button(buttons_frame3, text="🔫 ACTIVE SHOOTER / ARMED INTRUDER - SILVER", 
                                           command=self.send_active_shooter_alarm,
                                           bg='#bdc3c7', fg='black', 
                                           font=('Arial', 9, 'bold'),
                                    relief=tk.RAISED, bd=2)
        self.active_shooter_btn.pack(side=tk.LEFT)
        
        # Additional instructions frame
        instructions_frame = tk.Frame(quick_frame, bg='#34495e')
        instructions_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Checkbox for with instructions
        self.with_instructions_checkbox = tk.Checkbutton(instructions_frame, 
                                                       text="With Instructions", 
                                                       variable=self.with_instructions,
                                                       command=self.toggle_instructions,
                                       font=('Arial', 10, 'bold'),
                                                       fg='white', bg='#34495e',
                                                       selectcolor='#34495e',
                                                       activebackground='#34495e',
                                                       activeforeground='white')
        self.with_instructions_checkbox.pack(anchor=tk.W)
        
        # Instructions entry frame (initially hidden)
        self.instructions_entry_frame = tk.Frame(instructions_frame, bg='#34495e')
        self.instructions_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(self.instructions_entry_frame, text="Additional Instructions:", 
                                     font=('Arial', 10, 'bold'),
                fg='white', bg='#34495e').pack(anchor=tk.W)
        
        # Instructions entry
        instructions_input_frame = tk.Frame(self.instructions_entry_frame, bg='#34495e')
        instructions_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.instructions_entry = tk.Entry(instructions_input_frame, font=('Arial', 10), width=50)
        self.instructions_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.send_with_instructions_btn = tk.Button(instructions_input_frame, text="Send with Instructions", 
                                                   command=self.send_alarm_with_instructions,
                                                   bg='#27ae60', fg='white', 
                                                   font=('Arial', 10, 'bold'))
        self.send_with_instructions_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Initially hide the instructions frame
        self.instructions_entry_frame.pack_forget()
        
        # Log area
        log_frame = tk.Frame(main_frame, bg='#2c3e50')
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log title
        log_title = tk.Label(log_frame, text="Server Log", 
                           font=('Arial', 12, 'bold'), 
                           fg='white', bg='#2c3e50')
        log_title.pack(anchor=tk.W)
        
        # Scrolled text for logs
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 height=12, 
                                                 bg='#34495e', 
                                                 fg='white',
                                                 font=('Consolas', 9),
                                                 wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configure text tags for different message types
        self.log_text.tag_configure("info", foreground="#3498db", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("success", foreground="#27ae60", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("warning", foreground="#f39c12", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("error", foreground="#e74c3c", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("fire", foreground="#e74c3c", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("security", foreground="#f39c12", font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure("test", foreground="#3498db", font=('Consolas', 9, 'bold'))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        
        # Initial log message
        self.log_message("Alarm Server GUI initialized", "info")
        self.log_message("System tray will be available after 2 seconds", "info")
        
        # Update color preview
        self.update_color_preview()
        
        # Update floor display
        self.floor_display.config(text=self.selected_floor)
        
    def log_message(self, message, msg_type="info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.tag_add(msg_type, f"end-{len(log_entry.split(chr(10))[0])}c", "end-1c")
        self.log_text.see(tk.END)
    
    def authenticate_admin(self):
        """Authenticate admin user"""
        admin_name = self.admin_name_entry.get().strip()
        password = self.admin_pass_entry.get().strip()
        
        if not admin_name:
            messagebox.showwarning("Authentication Error", "Please enter admin name")
            return
            
        if not password:
            messagebox.showwarning("Authentication Error", "Please enter password")
            return
            
        if self.verify_password(password, self.admin_password):
            self.current_admin = admin_name
            self.is_authenticated = True
            
            # Update GUI
            self.admin_status_label.config(text=f"Authenticated as: {admin_name}", fg="#27ae60")
            self.login_btn.config(state=tk.DISABLED)
            self.logout_btn.config(state=tk.NORMAL)
            self.change_password_btn.config(state=tk.NORMAL)
            self.admin_name_entry.config(state=tk.DISABLED)
            self.admin_pass_entry.config(state=tk.DISABLED)
            
            self.log_message(f"Admin '{admin_name}' authenticated successfully", "success")
            messagebox.showinfo("Authentication Success", f"Welcome, {admin_name}!")
        else:
            self.log_message(f"Failed authentication attempt for '{admin_name}'", "error")
            messagebox.showerror("Authentication Failed", "Invalid password")
    
    def logout_admin(self):
        """Logout current admin"""
        if self.current_admin:
            self.log_message(f"Admin '{self.current_admin}' logged out", "info")
            
        self.current_admin = None
        self.is_authenticated = False
        
        # Update GUI
        self.admin_status_label.config(text="Not Authenticated", fg="#e74c3c")
        self.login_btn.config(state=tk.NORMAL)
        self.logout_btn.config(state=tk.DISABLED)
        self.change_password_btn.config(state=tk.DISABLED)
        self.admin_name_entry.config(state=tk.NORMAL)
        self.admin_pass_entry.config(state=tk.NORMAL)
        self.admin_name_entry.delete(0, tk.END)
        self.admin_pass_entry.delete(0, tk.END)
    
    def show_change_password_dialog(self):
        """Show password change dialog"""
        if not self.is_authenticated:
            messagebox.showwarning("Authentication Required", "Please login first")
            return
        
        # Create password change dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Admin Password")
        dialog.geometry("450x400")
        dialog.configure(bg='#2c3e50')
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = tk.Frame(dialog, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="Change Admin Password", 
                               font=('Arial', 16, 'bold'), 
                               fg='white', bg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Current password
        current_frame = tk.Frame(main_frame, bg='#2c3e50')
        current_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(current_frame, text="Current Password:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#2c3e50').pack(anchor=tk.W)
        
        current_pass_entry = tk.Entry(current_frame, font=('Arial', 10), width=30, show="*")
        current_pass_entry.pack(fill=tk.X, pady=(5, 0))
        
        # New password
        new_frame = tk.Frame(main_frame, bg='#2c3e50')
        new_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(new_frame, text="New Password:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#2c3e50').pack(anchor=tk.W)
        
        new_pass_entry = tk.Entry(new_frame, font=('Arial', 10), width=30, show="*")
        new_pass_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Confirm new password
        confirm_frame = tk.Frame(main_frame, bg='#2c3e50')
        confirm_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(confirm_frame, text="Confirm New Password:", 
                font=('Arial', 10, 'bold'), 
                fg='white', bg='#2c3e50').pack(anchor=tk.W)
        
        confirm_pass_entry = tk.Entry(confirm_frame, font=('Arial', 10), width=30, show="*")
        confirm_pass_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Password requirements
        requirements_label = tk.Label(main_frame, 
                                     text="Password must be at least 8 characters long", 
                                     font=('Arial', 9), 
                                     fg='#bdc3c7', bg='#2c3e50')
        requirements_label.pack(pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def change_password():
            current_password = current_pass_entry.get().strip()
            new_password = new_pass_entry.get().strip()
            confirm_password = confirm_pass_entry.get().strip()
            
            # Validate current password
            if not self.verify_password(current_password, self.admin_password):
                messagebox.showerror("Error", "Current password is incorrect")
                return
            
            # Validate new password
            if len(new_password) < 8:
                messagebox.showerror("Error", "New password must be at least 8 characters long")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("Error", "New passwords do not match")
                return
            
            # Change password
            if self.change_admin_password(new_password):
                messagebox.showinfo("Success", "Password changed successfully")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to change password")
        
        def cancel_change():
            dialog.destroy()
        
        # Change button
        change_btn = tk.Button(button_frame, text="Change Password", 
                             command=change_password,
                             bg='#27ae60', fg='white', 
                             font=('Arial', 10, 'bold'),
                             width=15, height=2)
        change_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                             command=cancel_change,
                             bg='#e74c3c', fg='white', 
                             font=('Arial', 10, 'bold'),
                             width=15, height=2)
        cancel_btn.pack(side=tk.LEFT)
        
        # Focus on current password field
        current_pass_entry.focus()
    
    def change_admin_password(self, new_password):
        """Change the admin password"""
        try:
            hashed_password = self.hash_password(new_password)
            if self.save_admin_password(hashed_password):
                self.admin_password = hashed_password
                self.log_message(f"Admin password changed by {self.current_admin}", "success")
                return True
            return False
        except Exception as e:
            self.log_message(f"Error changing password: {e}", "error")
            return False
    
    def check_admin_auth(self):
        """Check if admin is authenticated before allowing alarm operations"""
        if not self.is_authenticated:
            messagebox.showwarning("Authentication Required", 
                                 "Please authenticate as admin before sending alarms")
            return False
        return True
    
    def confirm_alarm_sending(self, message):
        """Show confirmation dialog before sending alarm"""
        result = messagebox.askyesno("Confirm Alarm", 
                                   f"Do you want to send this message?\n\n{message}")
        return result
    
    def update_clients_list(self):
        """Update the clients listbox"""
        self.clients_listbox.delete(0, tk.END)
        for i, client in enumerate(self.clients):
            try:
                address = client.getpeername()
                self.clients_listbox.insert(tk.END, f"Client {i+1}: {address[0]}:{address[1]}")
            except:
                self.clients_listbox.insert(tk.END, f"Client {i+1}: Unknown")
    
    def toggle_server(self):
        """Toggle server start/stop"""
        if self.running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        """Start the alarm server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
            self.running = True
            
            # Update GUI
            self.status_label.config(text="Server Running", fg="#27ae60")
            self.start_btn.config(text="Stop Server", bg="#e74c3c")
            self.log_message(f"Server started on {self.host}:{self.port}", "success")
            
            # Start client handler thread
            client_handler = threading.Thread(target=self.handle_clients)
            client_handler.daemon = True
            client_handler.start()
            
        except Exception as e:
            self.log_message(f"Failed to start server: {e}", "error")
            messagebox.showerror("Server Error", f"Failed to start server:\n{e}")
    
    def stop_server(self):
        """Stop the alarm server"""
        self.running = False
        if self.socket:
            self.socket.close()
        
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # Update GUI
        self.status_label.config(text="Server Stopped", fg="#e74c3c")
        self.start_btn.config(text="Start Server", bg="#27ae60")
        self.update_clients_list()
        self.log_message("Server stopped", "warning")
    
    def handle_clients(self):
        """Handle incoming client connections"""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                self.clients.append(client_socket)
                
                self.root.after(0, self.log_message, f"Client connected from {address}", "success")
                self.root.after(0, self.update_clients_list)
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    self.root.after(0, self.log_message, f"Error accepting client: {e}", "error")
    
    def handle_client(self, client_socket, address):
        """Handle individual client communication"""
        try:
            while self.running:
                # Send ping to keep connection alive
                client_socket.send(b"ping")
                time.sleep(30)  # Ping every 30 seconds
                
        except Exception as e:
            self.root.after(0, self.log_message, f"Client {address} disconnected: {e}", "warning")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            self.root.after(0, self.update_clients_list)
            client_socket.close()
    
    def broadcast_alarm(self, message, color, icon="⚠️", name="Custom Alarm"):
        """Broadcast alarm message to all connected clients"""
        if not self.running:
            messagebox.showwarning("Server Not Running", "Please start the server first")
            return
            
        if not self.clients:
            messagebox.showinfo("No Clients", "No clients are currently connected")
            return
            
        # Generate background and text colors based on the selected color
        bg_color = self.darken_color(color, 0.3)
        text_color = self.get_contrast_color(color)
        
        alarm_data = {
            "type": "custom",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "server": self.host,
            "color": color,
            "bg_color": bg_color,
            "text_color": text_color,
            "icon": icon,
            "name": name,
            "admin": self.current_admin if self.is_authenticated else "Unknown"
        }
        
        message_json = json.dumps(alarm_data).encode('utf-8')
        disconnected_clients = []
        sent_count = 0
        
        for client in self.clients:
            try:
                client.send(message_json)
                sent_count += 1
            except Exception as e:
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in self.clients:
                self.clients.remove(client)
                client.close()
        
        # Update GUI
        self.update_clients_list()
        admin_info = f" by {self.current_admin}" if self.is_authenticated else ""
        self.log_message(f"Alarm sent to {sent_count} clients: {message}{admin_info}", "success")
        
        if sent_count == 0:
            messagebox.showwarning("No Recipients", "Alarm was not sent to any clients")
    
    def darken_color(self, hex_color, factor):
        """Darken a hex color by a factor (0-1)"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Darken
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return '#2F4F4F'  # Default dark color
    
    def get_contrast_color(self, hex_color):
        """Get a contrasting text color (white or black) for a given background color"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Calculate luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Return white for dark colors, black for light colors
            return '#FFFFFF' if luminance < 0.5 else '#000000'
        except:
            return '#FFFFFF'  # Default to white
    
    def send_custom_alarm(self):
        """Send custom alarm message"""
        if not self.check_admin_auth():
            return
            
        message = self.message_entry.get().strip()
        if not message:
            messagebox.showwarning("Empty Message", "Please enter a message")
            return
            
        # Show confirmation dialog
        if not self.confirm_alarm_sending(message):
            return
            
        self.broadcast_alarm(message, self.selected_color)
        self.message_entry.delete(0, tk.END)
    
    def on_floor_changed(self, event=None):
        """Handle floor selection change"""
        self.selected_floor = self.floor_var.get()
        self.floor_display.config(text=self.selected_floor)
        self.log_message(f"Selected floor: {self.selected_floor}", "info")
    
    def choose_color(self):
        """Open color chooser for alarm color"""
        color = colorchooser.askcolor(color=self.selected_color, title="Choose Alarm Color")[1]
        if color:
            self.selected_color = color
            self.update_color_preview()
            self.log_message(f"Selected alarm color: {color}", "info")
    
    def update_color_preview(self):
        """Update the color preview box"""
        self.color_preview.config(bg=self.selected_color)
    
    
    def send_fire_alarm(self):
        """Send fire alarm"""
        if not self.check_admin_auth():
            return
        self.selected_alarm_type = "FIRE RESPONSE"
        
        if self.with_instructions.get():
            # Show instructions frame and wait for user input
            self.instructions_entry_frame.pack(fill=tk.X, pady=(5, 0))
            return
        
        message = f"FIRE ALARM - {self.selected_floor.upper()} - EVACUATE IMMEDIATELY"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#e74c3c", "🔥", "FIRE ALARM")
    
    def send_security_alarm(self):
        """Send security alarm"""
        if not self.check_admin_auth():
            return
        message = f"SECURITY ALERT - {self.selected_floor.upper()} - LOCKDOWN INITIATED"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#f39c12", "🛡️", "SECURITY ALERT")
    
    def send_test_alarm(self):
        """Send test alarm"""
        if not self.check_admin_auth():
            return
        message = f"TEST ALARM - {self.selected_floor.upper()} - SYSTEM CHECK"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#3498db", "🔔", "TEST ALARM")
    
    def send_code_blue_alarm(self):
        """Send Code Blue alarm"""
        if not self.check_admin_auth():
            return
        message = f"CODE BLUE - {self.selected_floor.upper()} - MEDICAL EMERGENCY"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#3498db", "🏥", "CODE BLUE")
    
    def send_code_black_alarm(self):
        """Send Code Black alarm"""
        if not self.check_admin_auth():
            return
        message = f"CODE BLACK - {self.selected_floor.upper()} - BOMB THREAT"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#000000", "💣", "CODE BLACK")
    
    def send_code_red_alarm(self):
        """Send Code Red alarm"""
        if not self.check_admin_auth():
            return
        message = f"CODE RED - {self.selected_floor.upper()} - FIRE EMERGENCY"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#e74c3c", "🔥", "CODE RED")
    
    def send_code_orange_alarm(self):
        """Send Code Orange alarm"""
        if not self.check_admin_auth():
            return
        message = f"CODE ORANGE - {self.selected_floor.upper()} - HAZARDOUS MATERIAL"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#f39c12", "☢️", "CODE ORANGE")
    
    def send_code_yellow_alarm(self):
        """Send Code Yellow alarm"""
        if not self.check_admin_auth():
            return
        message = f"CODE YELLOW - {self.selected_floor.upper()} - MISSING PERSON"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#f1c40f", "👤", "CODE YELLOW")
    
    def send_code_pink_alarm(self):
        """Send Code Pink alarm"""
        if not self.check_admin_auth():
            return
        message = f"CODE PINK - {self.selected_floor.upper()} - INFANT/CHILD EMERGENCY"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#e91e63", "👶", "CODE PINK")
    
    def send_code_gray_alarm(self):
        """Send Code Gray alarm"""
        if not self.check_admin_auth():
            return
        message = f"CODE GRAY - {self.selected_floor.upper()} - COMBATIVE PERSON"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#95a5a6", "⚔️", "CODE GRAY")
    
    def send_code_silver_alarm(self):
        """Send Code Silver alarm"""
        if not self.check_admin_auth():
            return
        message = f"CODE SILVER - {self.selected_floor.upper()} - ACTIVE SHOOTER"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#bdc3c7", "🔫", "CODE SILVER")
    
    def send_missing_child_alarm(self):
        """Send Missing Child/Abducted alarm"""
        if not self.check_admin_auth():
            return
        self.selected_alarm_type = "MISSING CHILD/ABDUCTED"
        
        if self.with_instructions.get():
            # Show instructions frame and wait for user input
            self.instructions_entry_frame.pack(fill=tk.X, pady=(5, 0))
            return
        
        message = f"MISSING CHILD/ABDUCTED - {self.selected_floor.upper()} - AMBER ALERT"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#f39c12", "👶", "MISSING CHILD/ABDUCTED")
    
    def send_missing_adult_alarm(self):
        """Send Missing Adult Patient alarm"""
        if not self.check_admin_auth():
            return
        self.selected_alarm_type = "MISSING ADULT PATIENT"
        
        if self.with_instructions.get():
            # Show instructions frame and wait for user input
            self.instructions_entry_frame.pack(fill=tk.X, pady=(5, 0))
            return
        
        message = f"MISSING ADULT PATIENT - {self.selected_floor.upper()} - YELLOW ALERT"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#f1c40f", "👤", "MISSING ADULT PATIENT")
    
    def send_bomb_threat_alarm(self):
        """Send Bomb Threat alarm"""
        if not self.check_admin_auth():
            return
        self.selected_alarm_type = "BOMB THREAT"
        
        if self.with_instructions.get():
            # Show instructions frame and wait for user input
            self.instructions_entry_frame.pack(fill=tk.X, pady=(5, 0))
            return
        
        message = f"BOMB THREAT - {self.selected_floor.upper()} - BLACK ALERT"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#2c3e50", "💣", "BOMB THREAT")
    
    def send_violent_situation_alarm(self):
        """Send Violent Situation alarm"""
        if not self.check_admin_auth():
            return
        self.selected_alarm_type = "VIOLENT SITUATION"
        
        if self.with_instructions.get():
            # Show instructions frame and wait for user input
            self.instructions_entry_frame.pack(fill=tk.X, pady=(5, 0))
            return
        
        message = f"VIOLENT SITUATION - {self.selected_floor.upper()} - GRAY ALERT"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#95a5a6", "⚔️", "VIOLENT SITUATION")
    
    def send_active_shooter_alarm(self):
        """Send Active Shooter/Armed Intruder alarm"""
        if not self.check_admin_auth():
            return
        self.selected_alarm_type = "ACTIVE SHOOTER/ARMED INTRUDER"
        
        if self.with_instructions.get():
            # Show instructions frame and wait for user input
            self.instructions_entry_frame.pack(fill=tk.X, pady=(5, 0))
            return
        
        message = f"ACTIVE SHOOTER/ARMED INTRUDER - {self.selected_floor.upper()} - SILVER ALERT"
        if not self.confirm_alarm_sending(message):
            return
        self.broadcast_alarm(message, "#bdc3c7", "🔫", "ACTIVE SHOOTER/ARMED INTRUDER")
    
    def toggle_instructions(self):
        """Toggle the instructions frame visibility"""
        if self.with_instructions.get():
            self.instructions_entry_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.instructions_entry_frame.pack_forget()
            # Clear the instructions field when hiding
            self.instructions_entry.delete(0, tk.END)
            self.selected_alarm_type = None
    
    def send_alarm_with_instructions(self):
        """Send alarm with additional instructions"""
        if not self.check_admin_auth():
            return
        
        if not self.selected_alarm_type:
            messagebox.showwarning("No Alarm Selected", "Please select an alarm type first by clicking one of the alarm buttons.")
            return
        
        instructions = self.instructions_entry.get().strip()
        if not instructions:
            messagebox.showwarning("No Instructions", "Please enter additional instructions.")
            return
        
        # Create the alarm message with instructions
        if self.selected_alarm_type == "FIRE RESPONSE":
            base_message = f"FIRE ALARM - {self.selected_floor.upper()} - EVACUATE IMMEDIATELY"
            color = "#e74c3c"
            icon = "🔥"
        elif self.selected_alarm_type == "MISSING CHILD/ABDUCTED":
            base_message = f"MISSING CHILD/ABDUCTED - {self.selected_floor.upper()} - AMBER ALERT"
            color = "#f39c12"
            icon = "👶"
        elif self.selected_alarm_type == "MISSING ADULT PATIENT":
            base_message = f"MISSING ADULT PATIENT - {self.selected_floor.upper()} - YELLOW ALERT"
            color = "#f1c40f"
            icon = "👤"
        elif self.selected_alarm_type == "BOMB THREAT":
            base_message = f"BOMB THREAT - {self.selected_floor.upper()} - BLACK ALERT"
            color = "#2c3e50"
            icon = "💣"
        elif self.selected_alarm_type == "VIOLENT SITUATION":
            base_message = f"VIOLENT SITUATION - {self.selected_floor.upper()} - GRAY ALERT"
            color = "#95a5a6"
            icon = "⚔️"
        elif self.selected_alarm_type == "ACTIVE SHOOTER/ARMED INTRUDER":
            base_message = f"ACTIVE SHOOTER/ARMED INTRUDER - {self.selected_floor.upper()} - SILVER ALERT"
            color = "#bdc3c7"
            icon = "🔫"
        else:
            base_message = f"{self.selected_alarm_type} - {self.selected_floor.upper()}"
            color = "#e74c3c"
            icon = "🚨"
        
        # Combine base message with instructions
        full_message = f"{base_message}\n\nINSTRUCTIONS: {instructions}"
        
        if not self.confirm_alarm_sending(full_message):
            return
        
        self.broadcast_alarm(full_message, color, icon, self.selected_alarm_type)
        
        # Clear the instructions field and hide the frame
        self.instructions_entry.delete(0, tk.END)
        self.selected_alarm_type = None
        self.instructions_entry_frame.pack_forget()
        self.with_instructions.set(False)
    
    def create_tray_icon(self):
        """Create a simple icon for the system tray"""
        # Create a simple icon image
        width = height = 64
        image = Image.new('RGB', (width, height), color='#2c3e50')
        dc = ImageDraw.Draw(image)
        
        # Draw a simple server icon
        dc.ellipse([16, 16, 48, 48], fill='#27ae60', outline='white', width=2)
        dc.text((20, 25), 'S', fill='white')
        
        return image
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        try:
            self.log_message("Setting up system tray...", "info")
            self.tray_status_label.config(text="System Tray: Setting up...", fg="#f39c12")
            
            icon_image = self.create_tray_icon()
            
            menu = pystray.Menu(
                pystray.MenuItem("Show Alarm Server", self.show_window),
                pystray.MenuItem("Exit", self.quit_application)
            )
            
            self.tray_icon = pystray.Icon(
                "Alarm Server",
                icon_image,
                "Alarm System Server",
                menu
            )
            
            # Start tray icon in a separate thread (like the client)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
            self.log_message("System tray icon created successfully", "info")
            self.tray_status_label.config(text="System Tray: Ready ✅", fg="#27ae60")
        except Exception as e:
            self.log_message(f"Error setting up system tray: {e}", "error")
            self.tray_status_label.config(text="System Tray: Failed ❌", fg="#e74c3c")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}", "error")
    
    def hide_to_tray(self):
        """Hide window to system tray"""
        self.is_hidden = True
        self.root.withdraw()  # Hide the window
        self.log_message("Server minimized to system tray", "info")
    
    def show_window(self, icon=None, item=None):
        """Show the main window from system tray"""
        self.is_hidden = False
        self.root.deiconify()  # Show the window
        self.root.lift()  # Bring to front
        self.root.focus_force()  # Focus the window
        self.log_message("Server restored from system tray", "info")
    
    
    def quit_application(self, icon=None, item=None):
        """Quit the application completely"""
        if self.running:
            self.stop_server()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
    
    def on_closing(self):
        """Handle window close event"""
        if self.running:
            self.stop_server()
        self.root.destroy()
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main function to run the alarm server with GUI"""
    try:
        print("Starting Alarm Server GUI...")
        server = AlarmServerGUI()
        print("GUI initialized successfully")
        print("Server is running in system tray.")
        print("You can close this console window - the server will continue running.")
        print("To stop the server, right-click the tray icon and select 'Exit'.")
        print()
        server.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        time.sleep(5)

if __name__ == "__main__":
    main()
