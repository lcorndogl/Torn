@echo off
REM Windows batch script to test the update_user_data lock mechanism

echo Update User Data - Lock Mechanism Test (Windows)
echo ==============================================
echo.

cd /d "%~dp0\Torn"
if errorlevel 1 (
    echo Error: Could not change to Torn directory
    pause
    exit /b 1
)

echo 1. Testing normal execution...
start /b python manage.py update_user_data
set FIRST_PID=%ERRORLEVEL%
echo Started first instance

timeout /t 3 /nobreak > nul

echo.
echo 2. Testing second instance (should be blocked)...
python manage.py update_user_data
echo Second instance completed

echo.
echo 3. Testing --force option...
start /b python manage.py update_user_data
timeout /t 3 /nobreak > nul

echo.
echo 4. Testing force execution...
python manage.py update_user_data --force
echo Force execution completed

echo.
echo Test completed!

REM Check if lock file exists
set TEMP_DIR=%TEMP%
if exist "%TEMP_DIR%\update_user_data.pid" (
    echo Warning: Lock file still exists at %TEMP_DIR%\update_user_data.pid
    type "%TEMP_DIR%\update_user_data.pid"
) else (
    echo ✓ Lock file properly cleaned up
)

pause
