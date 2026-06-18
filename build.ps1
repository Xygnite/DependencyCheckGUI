# Build script for DependencyCheckGUI (PowerShell version)
# Run with: powershell -ExecutionPolicy Bypass -File build.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DependencyCheckGUI Build Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Step 1: Install dependencies
Write-Host "Step 1: Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed successfully." -ForegroundColor Green
Write-Host ""

# Step 2: Clean previous builds
Write-Host "Step 2: Cleaning previous builds..." -ForegroundColor Cyan
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "DependencyCheckGUI.spec") { Remove-Item "DependencyCheckGUI.spec" -Force }
Write-Host "Previous builds cleaned." -ForegroundColor Green
Write-Host ""

# Step 3: Build the executable
Write-Host "Step 3: Building executable (this may take a few minutes)..." -ForegroundColor Cyan
pyinstaller build.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The executable is located at:" -ForegroundColor Cyan
Write-Host "  dist\DependencyCheckGUI.exe" -ForegroundColor Yellow
Write-Host ""
Write-Host "All assets (stylesheets, configuration, images) are included." -ForegroundColor Green
Write-Host ""
