@echo off

echo =============================================
echo   ParallelMonitor - Build Script
echo =============================================
echo.

REM --- 1. Check Python ---
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.9+
    pause
    exit /b 1
)
echo        OK

REM --- 2. Install deps ---
echo.
echo [2/5] Installing dependencies...
pip install -r requirements.txt --upgrade --quiet --no-warn-script-location
if errorlevel 1 (
    echo.
    echo [ERROR] pip install failed.
    echo.
    echo This is likely caused by Windows Long Path limit.
    echo To fix, run the following command as Administrator:
    echo.
    echo   reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f
    echo.
    echo Then RESTART your PC and re-run build.bat.
    pause
    exit /b 1
)
echo        Done

REM --- 3. Install PyInstaller ---
echo.
echo [3/5] Installing PyInstaller...
pip install pyinstaller --upgrade --quiet --no-warn-script-location
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller
    pause
    exit /b 1
)
echo        Done

REM --- 4. Clean ---
echo.
echo [4/5] Cleaning old builds...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
echo        Done

REM --- 5. Build ---
echo.
echo [5/5] Building (may take a few minutes)...
echo.

python -m PyInstaller ParallelMonitor.spec

if errorlevel 1 (
    echo.
    echo =============================================
    echo   BUILD FAILED!
    echo   Common issues:
    echo   1. Antivirus deleted temp files - disable AV and retry
    echo   2. Path with non-ASCII chars - use plain ASCII path
    echo   3. Dependency conflict - build in a virtualenv
    echo =============================================
    pause
    exit /b 1
)

echo.
echo =============================================
echo   BUILD SUCCESS!
echo   Output: dist\ParallelMonitor.exe
echo.
echo   Requirements to run:
echo          - Edge or Chrome installed on target PC
echo          - No Python or Playwright needed
echo =============================================
echo.

start "" "dist"
pause
