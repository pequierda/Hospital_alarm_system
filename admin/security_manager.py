#!/usr/bin/env python3
"""
Security Manager for Alarm System
Enhanced security features for password management
"""

import hashlib
import secrets
import string
import os
import sys
import datetime

def hash_password(password):
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def generate_secure_password(length=12):
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def create_security_log(message):
    """Create security log entry"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] SECURITY: {message}\n"
    
    try:
        with open("security.log", "a") as f:
            f.write(log_entry)
    except:
        pass

def reset_admin_password():
    """Reset admin password with security logging"""
    password_file = "admin_password.txt"
    
    # Generate new secure password
    new_password = generate_secure_password()
    hashed_password = hash_password(new_password)
    
    # Log security event
    create_security_log(f"Password reset initiated by user")
    
    # Save to file
    try:
        with open(password_file, 'w') as f:
            f.write(hashed_password)
        
        print("=" * 80)
        print("SECURITY ALERT - ADMIN PASSWORD RESET")
        print("=" * 80)
        print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"New admin password: {new_password}")
        print("=" * 80)
        print("⚠️  SECURITY WARNING:")
        print("   - This password reset has been logged")
        print("   - Save this password securely")
        print("   - Change it immediately after first login")
        print("   - Monitor for unauthorized access")
        print("=" * 80)
        
        # Log the password reset
        create_security_log(f"Password reset completed - new password generated")
        
        return True
    except Exception as e:
        create_security_log(f"Password reset failed: {e}")
        print(f"Error resetting password: {e}")
        return False

def check_security_status():
    """Check current security status"""
    password_file = "admin_password.txt"
    security_log = "security.log"
    
    print("=" * 60)
    print("ALARM SYSTEM SECURITY STATUS")
    print("=" * 60)
    
    # Check password file
    if os.path.exists(password_file):
        print("✅ Password file: EXISTS")
        try:
            with open(password_file, 'r') as f:
                content = f.read().strip()
                if ':' in content and len(content) > 50:
                    print("✅ Password format: VALID (hashed)")
                else:
                    print("❌ Password format: INVALID (not properly hashed)")
        except:
            print("❌ Password file: CORRUPTED")
    else:
        print("❌ Password file: MISSING (SECURITY RISK!)")
    
    # Check security log
    if os.path.exists(security_log):
        print("✅ Security log: EXISTS")
        try:
            with open(security_log, 'r') as f:
                lines = f.readlines()
                print(f"📊 Security events logged: {len(lines)}")
                if lines:
                    print(f"📅 Last event: {lines[-1].strip()}")
        except:
            print("❌ Security log: CORRUPTED")
    else:
        print("ℹ️  Security log: NOT CREATED YET")
    
    print("=" * 60)

def view_security_log():
    """View security log"""
    security_log = "security.log"
    
    if not os.path.exists(security_log):
        print("No security log found.")
        return
    
    print("=" * 60)
    print("SECURITY LOG")
    print("=" * 60)
    
    try:
        with open(security_log, 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:  # Show last 20 entries
                print(line.strip())
    except Exception as e:
        print(f"Error reading security log: {e}")
    
    print("=" * 60)

def main():
    """Main function"""
    print("Alarm System Security Manager")
    print("=" * 40)
    print("1. Check security status")
    print("2. Reset admin password")
    print("3. View security log")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            check_security_status()
        elif choice == "2":
            if reset_admin_password():
                print("\n✅ Password reset successfully!")
            else:
                print("\n❌ Failed to reset password!")
        elif choice == "3":
            view_security_log()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()
