#!/usr/bin/env python
"""
Test script specifically for testing the lock mechanism with concurrent execution.
"""

import subprocess
import time
import os
import sys
import platform

def test_windows_lock():
    """Test the lock mechanism on Windows."""
    print("Testing Windows lock mechanism...")
    
    # Start first instance
    print("Starting first instance...")
    proc1 = subprocess.Popen(
        [sys.executable, "test_lock_simple.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for it to acquire the lock
    time.sleep(2)
    
    # Start second instance (should be blocked)
    print("Starting second instance (should be blocked)...")
    proc2 = subprocess.run(
        [sys.executable, "test_lock_simple.py"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    print(f"Second instance return code: {proc2.returncode}")
    print(f"Second instance stdout: {proc2.stdout}")
    print(f"Second instance stderr: {proc2.stderr}")
    
    # Check if second instance was blocked
    if "Another instance of test_update_user_data is already running" in proc2.stdout:
        print("✓ Lock mechanism working - second instance was blocked")
    else:
        print("✗ Lock mechanism failed - second instance was not blocked")
    
    # Test force option
    print("\nTesting --force option...")
    proc3 = subprocess.run(
        [sys.executable, "test_lock_simple.py", "--force"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    print(f"Force instance return code: {proc3.returncode}")
    print(f"Force instance stdout: {proc3.stdout}")
    
    if "Force execution enabled" in proc3.stdout:
        print("✓ Force option working")
    else:
        print("✗ Force option not working")
    
    # Clean up first instance
    proc1.terminate()
    proc1.wait()
    
    print("Test completed!")

if __name__ == "__main__":
    test_windows_lock()
