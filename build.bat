@echo off
REM Build script for DependencyCheckGUI
REM This script builds the project into a single .exe file with all assets

echo.
echo ========================================
echo DependencyCheckGUI Build Script
echo ========================================
echo.

REM Step 1: Install dependencies
echo Step 1: Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install dependencies
    exit /b 1
)
echo Dependencies installed successfully.
echo.

REM Step 2: Clean previous builds
echo Step 2: Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist DependencyCheckGUI.spec del DependencyCheckGUI.spec
echo Previous builds cleaned.
echo.

REM Step 3: Build the executable
echo Step 3: Building executable (this may take a few minutes)...
pyinstaller build.spec

if %ERRORLEVEL% NEQ 0 (
    echo Error: Build failed
    exit /b 1
)
echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo The executable is located at:
echo   dist\DependencyCheckGUI.exe
echo.
echo All assets (stylesheets, configuration, images) are included.
echo.
pause
