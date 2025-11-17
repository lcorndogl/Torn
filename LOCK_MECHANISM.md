# Update User Data - Lock Mechanism

This document explains how to prevent multiple instances of the `update_user_data` management command from running simultaneously.

## Overview

The `update_user_data` Django management command now includes a built-in lock mechanism that prevents multiple instances from running at the same time. This is important because:

1. **API Rate Limiting**: Running multiple instances could exceed API rate limits
2. **Database Conflicts**: Concurrent database operations could cause conflicts
3. **Resource Usage**: Multiple instances would consume unnecessary system resources

## How It Works

The lock mechanism uses a combination of:
- **PID (Process ID) file**: `/tmp/update_user_data.pid`
- **File locking**: Using `fcntl` when available (Unix/Linux systems)
- **Process validation**: Checking if the process in the PID file is still running

## Usage

### Normal Usage
```bash
python manage.py update_user_data
```

If another instance is already running, you'll see:
```
Another instance of update_user_data is already running. Skipping execution.
Use --force to override this check.
```

### Force Execution
To bypass the lock check (use with caution):
```bash
python manage.py update_user_data --force
```

### Cron Job Setup
For automated execution via cron, the lock mechanism prevents overlapping runs:

```bash
# Add to crontab (crontab -e)
# Run every hour
0 * * * * cd /path/to/your/project && python manage.py update_user_data
```

## Lock File Location

- **Default**: `/tmp/update_user_data.pid`
- **Contains**: Process ID of the running instance
- **Cleanup**: Automatically removed when the script completes normally

## Error Handling

The lock mechanism handles several scenarios:

1. **Stale Lock Files**: If a PID file exists but the process isn't running, the file is automatically removed
2. **Signal Handling**: SIGINT (Ctrl+C) and SIGTERM are handled gracefully with proper cleanup
3. **Exception Handling**: Lock is released even if an exception occurs during execution

## Testing the Lock Mechanism

### Manual Testing
1. Run the command in one terminal:
   ```bash
   python manage.py update_user_data
   ```
2. While it's running, try to run it in another terminal:
   ```bash
   python manage.py update_user_data
   ```
3. The second instance should be blocked

### Automated Testing
Use the provided test scripts:

**Cross-platform Python test (recommended):**
```bash
python test_lock_crossplatform.py
```

**Linux/macOS Bash test:**
```bash
./test_lock.sh
```

**Windows Batch test:**
```cmd
test_lock_windows.bat
```

## Systemd Service (Optional)

For production deployments, you can create a systemd service:

```ini
[Unit]
Description=Update User Data Service
After=network.target

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/python manage.py update_user_data
Environment=DJANGO_SETTINGS_MODULE=your_project.settings

[Install]
WantedBy=multi-user.target
```

And a timer for regular execution:

```ini
[Unit]
Description=Update User Data Timer
Requires=update-user-data.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

## Troubleshooting

### Lock File Stuck
**On Linux/macOS:**
```bash
# Check if the process is still running
cat /tmp/update_user_data.pid
ps aux | grep <PID>

# If not running, remove the lock file
rm /tmp/update_user_data.pid
```

**On Windows:**
```cmd
# Check if the process is still running
type %TEMP%\update_user_data.pid
tasklist /FI "PID eq <PID>"

# If not running, remove the lock file
del %TEMP%\update_user_data.pid
```

### Debugging
To see detailed output and timing:
```bash
python manage.py update_user_data --verbosity=2
```

### Force Override
If you need to run multiple instances for testing:
```bash
python manage.py update_user_data --force
```

## Security Considerations

1. **File Permissions**: The `/tmp` directory is world-writable, but the PID file is created with appropriate permissions
2. **Process Validation**: The mechanism validates that the PID in the file corresponds to an actual running process
3. **Signal Handling**: Proper cleanup prevents zombie processes and stuck locks

## Platform Compatibility

The lock mechanism works on:
- ✅ Linux (Ubuntu, CentOS, etc.) - Full functionality
- ✅ macOS - Full functionality  
- ✅ Unix-like systems - Full functionality
- ✅ Windows - Core functionality (see Windows-specific notes below)

### Windows-Specific Notes

On Windows, the lock mechanism works with these adaptations:

1. **Lock File Location**: Uses `%TEMP%\update_user_data.pid` instead of `/tmp/update_user_data.pid`
2. **Process Detection**: Uses `tasklist` command instead of `os.kill(pid, 0)`
3. **No File Locking**: `fcntl` module is not available, so only PID file locking is used
4. **Signal Handling**: Only `SIGINT` (Ctrl+C) is supported, not `SIGTERM`

Despite these differences, the core functionality remains the same:
- ✅ Prevents multiple instances from running
- ✅ Automatically cleans up stale lock files
- ✅ Supports `--force` option
- ✅ Graceful cleanup on interruption
