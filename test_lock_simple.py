#!/usr/bin/env python
"""
Test version of update_user_data that just tests the lock mechanism
without doing any actual API calls or database operations.
"""

import os
import sys
import time
import tempfile
import platform
import signal

# Add the Django project to the path
django_path = os.path.join(os.path.dirname(__file__), 'Torn')
sys.path.insert(0, django_path)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Torn.settings')

# Try to import fcntl for Unix systems, handle gracefully if not available
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

class TestLockCommand:
    """Simplified version of the Django command for testing locks only."""
    
    def __init__(self):
        self.lock_file = None
        
        # Use platform-appropriate temp directory and file name
        if platform.system() == 'Windows':
            temp_dir = tempfile.gettempdir()
            self.pid_file_path = os.path.join(temp_dir, 'test_update_user_data.pid')
        else:
            self.pid_file_path = '/tmp/test_update_user_data.pid'
        
        # Register signal handlers for graceful cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # SIGTERM is not available on Windows
        if platform.system() != 'Windows':
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle signals for graceful cleanup."""
        print(f'Received signal {signum}. Cleaning up and exiting...')
        self.release_lock()
        sys.exit(0)

    def __del__(self):
        """Destructor to ensure lock is always released."""
        self.release_lock()

    def acquire_lock(self):
        """
        Acquire a file lock to prevent multiple instances from running.
        Returns True if lock is acquired, False if another instance is running.
        """
        try:
            # Check if PID file exists and if the process is still running
            if os.path.exists(self.pid_file_path):
                with open(self.pid_file_path, 'r') as f:
                    try:
                        existing_pid = int(f.read().strip())
                        # Check if process is still running
                        if self._is_process_running(existing_pid):
                            return False  # Process is still running
                        else:
                            # PID file is stale, remove it
                            os.remove(self.pid_file_path)
                    except (ValueError, OSError):
                        # Invalid PID file, remove it
                        os.remove(self.pid_file_path)
            
            # Create or open the PID file
            self.lock_file = open(self.pid_file_path, 'w')
            
            # Try to acquire an exclusive lock (only on Unix-like systems)
            if HAS_FCNTL:
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    # Lock could not be acquired
                    self.lock_file.close()
                    return False
            
            # Write the current process ID to the file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()
            
            return True
            
        except (IOError, OSError):
            # Lock could not be acquired (another instance is running)
            if self.lock_file:
                self.lock_file.close()
            return False

    def _is_process_running(self, pid):
        """Check if a process with given PID is running."""
        try:
            if platform.system() == 'Windows':
                # On Windows, use tasklist command to check if process exists
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV'],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                # On Unix-like systems, sending signal 0 checks if process exists
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.SubprocessError, ImportError):
            return False

    def release_lock(self):
        """Release the file lock and clean up."""
        if self.lock_file:
            try:
                # Try to release flock if it was used (Unix only)
                if HAS_FCNTL:
                    try:
                        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                    except (IOError, OSError):
                        pass
                self.lock_file.close()
                self.lock_file = None
                # Remove the PID file
                if os.path.exists(self.pid_file_path):
                    os.remove(self.pid_file_path)
            except (IOError, OSError):
                pass

    def run(self, force=False):
        """Main execution method."""
        # Check if --force option was provided
        if not force and not self.acquire_lock():
            print('Another instance of test_update_user_data is already running. Skipping execution.')
            print('Use --force to override this check.')
            return
        elif force:
            # If forced, still try to acquire lock but don't fail if we can't
            if not self.acquire_lock():
                print('Force execution enabled. Running despite existing instance.')

        # Log start of execution
        print(f'Starting test_update_user_data script at {time.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'PID: {os.getpid()}')
        print(f'Lock file: {self.pid_file_path}')

        try:
            # Simulate some work (instead of actual API calls)
            print('Simulating work...')
            time.sleep(5)
            print('Work completed successfully!')
        except Exception as e:
            print(f'An error occurred during execution: {str(e)}')
            raise
        finally:
            # Always release the lock when done
            self.release_lock()
            print(f'Completed test_update_user_data script at {time.strftime("%Y-%m-%d %H:%M:%S")}')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Test the lock mechanism')
    parser.add_argument('--force', action='store_true', help='Force execution even if another instance is running')
    args = parser.parse_args()
    
    cmd = TestLockCommand()
    cmd.run(force=args.force)
