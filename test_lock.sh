#!/bin/bash

# Simple test script for the update_user_data lock mechanism
# This script demonstrates how to use the management command and test the locking

echo "Update User Data - Lock Mechanism Test"
echo "======================================"

cd "$(dirname "$0")/Torn" || {
    echo "Error: Could not change to Torn directory"
    exit 1
}

echo ""
echo "1. Testing normal execution..."
python3 manage.py update_user_data &
FIRST_PID=$!
echo "Started first instance (PID: $FIRST_PID)"

sleep 3

echo ""
echo "2. Testing second instance (should be blocked)..."
python3 manage.py update_user_data
echo "Second instance completed"

echo ""
echo "3. Waiting for first instance to complete..."
wait $FIRST_PID
echo "First instance completed"

echo ""
echo "4. Testing --force option..."
python3 manage.py update_user_data &
THIRD_PID=$!
echo "Started third instance (PID: $THIRD_PID)"

sleep 3

echo ""
echo "5. Testing force execution..."
python3 manage.py update_user_data --force
echo "Force execution completed"

echo ""
echo "Cleaning up..."
kill $THIRD_PID 2>/dev/null
wait $THIRD_PID 2>/dev/null

echo ""
echo "Test completed!"

# Check if lock file exists (it shouldn't after cleanup)
if [ -f "/tmp/update_user_data.pid" ]; then
    echo "Warning: Lock file still exists at /tmp/update_user_data.pid"
    echo "Content: $(cat /tmp/update_user_data.pid)"
else
    echo "✓ Lock file properly cleaned up"
fi
