#!/usr/bin/env python3
"""
Cross-platform test script to verify that the update_user_data lock mechanism works.
This script works on both Windows and Unix-like systems.
"""

import subprocess
import time
import os
import sys
import platform

def get_django_command():
    """Get the appropriate Django management command for the current platform."""
    django_dir = "Torn"
    if not os.path.exists(django_dir):
        print(f"Error: Django project directory '{django_dir}' not found!")
        return None, None
    
    # Use python instead of python3 on Windows
    if platform.system() == 'Windows':
        python_cmd = "python"
    else:
        python_cmd = sys.executable
    
    return [python_cmd, "manage.py", "update_user_data"], django_dir

def test_concurrent_execution():
    """Test that only one instance can run at a time."""
    print("Testing concurrent execution of update_user_data...")
    
    cmd, django_dir = get_django_command()
    if not cmd:
        return False
    
    print(f"Platform: {platform.system()}")
    print(f"Using command: {' '.join(cmd)}")
    
    print("Starting first instance...")
    # Start first instance in background
    try:
        proc1 = subprocess.Popen(
            cmd,
            cwd=django_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        print(f"Error starting first instance: {e}")
        return False
    
    # Wait a moment for it to start and acquire lock
    time.sleep(3)
    
    print("Starting second instance (should be blocked)...")
    # Try to start second instance
    try:
        proc2 = subprocess.run(
            cmd,
            cwd=django_dir,
            capture_output=True,
            text=True,
            timeout=15
        )
    except subprocess.TimeoutExpired:
        print("✗ Second instance timed out (this might indicate a problem)")
        proc1.terminate()
        return False
    except Exception as e:
        print(f"Error running second instance: {e}")
        proc1.terminate()
        return False
    
    # Check if second instance was properly blocked
    if "Another instance of update_user_data is already running" in proc2.stdout:
        print("✓ Lock mechanism working correctly - second instance was blocked")
        success = True
    else:
        print("✗ Lock mechanism failed - second instance was not blocked")
        print(f"Second instance stdout: {proc2.stdout}")
        print(f"Second instance stderr: {proc2.stderr}")
        success = False
    
    # Clean up first instance
    print("Cleaning up first instance...")
    proc1.terminate()
    try:
        proc1.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print("Force killing first instance...")
        proc1.kill()
        proc1.wait()
    
    return success

def test_force_execution():
    """Test that --force option bypasses the lock."""
    print("\nTesting --force option...")
    
    cmd, django_dir = get_django_command()
    if not cmd:
        return False
    
    cmd_force = cmd + ["--force"]
    
    print("Starting first instance...")
    # Start first instance in background
    try:
        proc1 = subprocess.Popen(
            cmd,
            cwd=django_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        print(f"Error starting first instance: {e}")
        return False
    
    # Wait for it to start
    time.sleep(3)
    
    print("Starting second instance with --force...")
    # Try to start second instance with --force
    try:
        proc2 = subprocess.run(
            cmd_force,
            cwd=django_dir,
            capture_output=True,
            text=True,
            timeout=30  # Increased timeout for Windows
        )
    except subprocess.TimeoutExpired:
        print("✗ Force instance timed out")
        proc1.terminate()
        return False
    except Exception as e:
        print(f"Error running force instance: {e}")
        proc1.terminate()
        return False
    
    # Check if --force option worked
    print(f"Force instance return code: {proc2.returncode}")
    print(f"Force instance stdout: {proc2.stdout[:200]}...")  # First 200 chars
    
    if "Force execution enabled" in proc2.stdout or "Starting update_user_data script" in proc2.stdout:
        print("✓ Force option working correctly")
        success = True
    else:
        print("✗ Force option not working as expected")
        print(f"Full force instance stdout: {proc2.stdout}")
        print(f"Force instance stderr: {proc2.stderr}")
        success = False
    
    # Clean up
    print("Cleaning up...")
    proc1.terminate()
    try:
        proc1.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc1.kill()
        proc1.wait()
    
    return success

def test_lock_file_location():
    """Test that the lock file is created in the correct location."""
    print("\nTesting lock file location...")
    
    if platform.system() == 'Windows':
        import tempfile
        expected_location = os.path.join(tempfile.gettempdir(), 'update_user_data.pid')
        print(f"Expected lock file location on Windows: {expected_location}")
    else:
        expected_location = "/tmp/update_user_data.pid"
        print(f"Expected lock file location on Unix: {expected_location}")
    
    # Clean up any existing lock file
    if os.path.exists(expected_location):
        try:
            os.remove(expected_location)
            print("Removed existing lock file")
        except:
            pass
    
    cmd, django_dir = get_django_command()
    if not cmd:
        return False
    
    # Start instance and quickly check for lock file
    proc = subprocess.Popen(
        cmd,
        cwd=django_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for lock file to be created
    time.sleep(2)
    
    if os.path.exists(expected_location):
        print("✓ Lock file created at expected location")
        success = True
        
        # Check if PID is correct
        try:
            with open(expected_location, 'r') as f:
                pid_in_file = int(f.read().strip())
            if pid_in_file == proc.pid:
                print(f"✓ Correct PID ({pid_in_file}) written to lock file")
            else:
                print(f"✗ Incorrect PID in lock file. Expected: {proc.pid}, Found: {pid_in_file}")
        except Exception as e:
            print(f"✗ Error reading PID from lock file: {e}")
    else:
        print("✗ Lock file not created at expected location")
        success = False
    
    # Clean up
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    
    # Verify lock file is cleaned up
    time.sleep(1)
    if not os.path.exists(expected_location):
        print("✓ Lock file properly cleaned up after process termination")
    else:
        print("✗ Lock file not cleaned up")
        success = False
    
    return success

if __name__ == "__main__":
    print("Testing update_user_data lock mechanism")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print()
    
    # Test basic locking
    test1_passed = test_concurrent_execution()
    
    # Test force option
    test2_passed = test_force_execution()
    
    # Test lock file handling
    test3_passed = test_lock_file_location()
    
    print(f"\nTest Results:")
    print(f"Concurrent execution test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Force option test: {'PASSED' if test2_passed else 'FAILED'}")
    print(f"Lock file location test: {'PASSED' if test3_passed else 'FAILED'}")
    
    if test1_passed and test2_passed and test3_passed:
        print(f"\n✓ All tests passed! Lock mechanism is working correctly on {platform.system()}.")
        sys.exit(0)
    else:
        print(f"\n✗ Some tests failed on {platform.system()}. Please check the implementation.")
        sys.exit(1)
