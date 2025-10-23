# Alarm System Security Guide

## Overview
The alarm system uses a comprehensive security management system with the following features:

- **Secure password hashing**: SHA-256 with salt
- **File deletion protection**: Server won't start if password file is missing
- **Security logging**: All events tracked with timestamps
- **Audit trail**: Complete history of security events
- **Manual intervention**: No auto-password generation

## Security Tools

### Primary Tool: `security_manager.py`
**Use this for all password management:**

```bash
python security_manager.py
```

**Features:**
1. **Check security status** - Verify system security
2. **Reset admin password** - Secure password reset with logging
3. **View security log** - Audit trail of all events
4. **Exit** - Close the tool

### What Happens if Password File is Deleted

#### ✅ **SECURE BEHAVIOR:**
1. **Server refuses to start**
2. **Security alert displayed**
3. **No auto-password generation**
4. **Manual intervention required**
5. **All events logged**

#### ❌ **OLD INSECURE BEHAVIOR (Fixed):**
- Server would auto-generate new password
- Password displayed in logs
- Hacker could gain immediate access

## Password Management

### First Time Setup
1. Run: `python security_manager.py`
2. Choose option 2: "Reset admin password"
3. Save the generated password securely
4. Start the server: `python alarm_server_gui.py`

### Changing Passwords
1. Login to server GUI with current password
2. Click "Change Password" button
3. Enter current password
4. Enter new password (minimum 8 characters)
5. Confirm new password
6. Click "Change Password"

### Password Requirements
- Minimum 8 characters
- Can include letters, numbers, and special characters
- Case sensitive
- Must be confirmed before saving

## Security Features

### File Protection
- **Password file**: `admin_password.txt` (hashed, never plain text)
- **Security log**: `security.log` (audit trail)
- **File deletion protection**: Server won't start if password file missing

### Security Logging
All security events are logged with timestamps:
- Password resets
- Login attempts
- Security alerts
- File access events

### Audit Trail
Use `security_manager.py` option 3 to view:
- All security events
- Timestamps
- Event descriptions
- Last 20 events displayed

## Troubleshooting

### Server Won't Start
**Error**: "Admin password file is missing"
**Solution**:
1. Run: `python security_manager.py`
2. Choose option 2: "Reset admin password"
3. Save the new password
4. Restart server

### Forgot Password
**Solution**:
1. Run: `python security_manager.py`
2. Choose option 2: "Reset admin password"
3. Use the new password to login
4. Change password through GUI

### Security Concerns
**If you suspect unauthorized access**:
1. Check security log: `python security_manager.py` → option 3
2. Look for suspicious events
3. Reset password immediately
4. Monitor system access

## File Structure

```
OSH/
├── alarm_server_gui.py          # Main server (secure)
├── alarm_client.py             # Client application
├── security_manager.py         # Security management tool
├── admin_password.txt          # Hashed password (auto-generated)
├── security.log               # Security audit log (auto-generated)
└── SECURITY_GUIDE.md          # This documentation
```

## Security Best Practices

### Password Security
1. **Use strong passwords**: 12+ characters with mixed case, numbers, symbols
2. **Change regularly**: Update passwords periodically
3. **Don't share**: Keep passwords confidential
4. **Monitor access**: Check security logs regularly

### System Security
1. **Secure file permissions**: Protect password and log files
2. **Regular backups**: Backup security files
3. **Monitor logs**: Check for suspicious activity
4. **Update regularly**: Keep system updated

### Incident Response
1. **Check security log**: Look for unauthorized access
2. **Reset password**: If compromise suspected
3. **Monitor system**: Watch for unusual activity
4. **Document events**: Record security incidents

## Technical Details

### Password Hashing
```
Format: salt:hash
- salt: 32-character hexadecimal string
- hash: 64-character SHA-256 hash of (password + salt)
```

### Security Events Logged
- Password resets
- Login attempts
- File access
- Security alerts
- System errors

### File Protection
- Password file must exist for server to start
- No auto-generation if file missing
- Manual intervention required for password reset
- All events logged for audit trail

This security system prevents unauthorized access and provides comprehensive audit trails for security monitoring.
