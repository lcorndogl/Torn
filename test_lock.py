#!/usr/bin/env python3
"""
Simple test script to verify that the update_user_data lock mechanism works.
This script simulates running multiple instances to test the locking behavior.
"""

import subprocess
import time
import os
import sys

def test_concurrent_execution():
    """Test that only one instance can run at a time."""
    print("Testing concurrent execution of update_user_data...")
    
    # Change to the Django project directory
    django_dir = "Torn"
    if not os.path.exists(django_dir):
        print(f"Error: Django project directory '{django_dir}' not found!")
        return False
    
    # Command to run the management command
    cmd = [sys.executable, "manage.py", "update_user_data"]
    
    print("Starting first instance...")
    # Start first instance in background
    proc1 = subprocess.Popen(
        cmd,
        cwd=django_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for it to start and acquire lock
    time.sleep(2)
    
    print("Starting second instance (should be blocked)...")
    # Try to start second instance
    proc2 = subprocess.run(
        cmd,
        cwd=django_dir,
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Check if second instance was properly blocked
    if "Another instance of update_user_data is already running" in proc2.stdout:
        print("✓ Lock mechanism working correctly - second instance was blocked")
        success = True
    else:
        print("✗ Lock mechanism failed - second instance was not blocked")
        print(f"Second instance output: {proc2.stdout}")
        success = False
    
    # Clean up first instance
    proc1.terminate()
    try:
        proc1.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc1.kill()
        proc1.wait()
    
    return success

def test_force_execution():
    """Test that --force option bypasses the lock."""
    print("\nTesting --force option...")
    
    django_dir = "Torn"
    cmd_normal = [sys.executable, "manage.py", "update_user_data"]
    cmd_force = [sys.executable, "manage.py", "update_user_data", "--force"]
    
    print("Starting first instance...")
    # Start first instance in background
    proc1 = subprocess.Popen(
        cmd_normal,
        cwd=django_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for it to start
    time.sleep(2)
    
    print("Starting second instance with --force...")
    # Try to start second instance with --force
    proc2 = subprocess.run(
        cmd_force,
        cwd=django_dir,
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Check if --force option worked
    if "Force execution enabled" in proc2.stdout:
        print("✓ Force option working correctly")
        success = True
    else:
        print("✗ Force option not working as expected")
        print(f"Second instance output: {proc2.stdout}")
        success = False
    
    # Clean up
    proc1.terminate()
    try:
        proc1.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc1.kill()
        proc1.wait()
    
    return success

if __name__ == "__main__":
    print("Testing update_user_data lock mechanism\n")
    
    # Test basic locking
    test1_passed = test_concurrent_execution()
    
    # Test force option
    test2_passed = test_force_execution()
    
    print(f"\nTest Results:")
    print(f"Concurrent execution test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Force option test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✓ All tests passed! Lock mechanism is working correctly.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please check the implementation.")
        sys.exit(1)
