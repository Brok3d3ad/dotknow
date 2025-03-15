@echo off
echo Building SVG Processor with custom icon...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing required packages...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
)

REM Remove any existing build and dist folders to ensure clean build
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building application using PyInstaller with custom icon...
pyinstaller autStand_icon.spec

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

REM Refresh the icon cache
echo Refreshing icon cache...
ie4uinit.exe -ClearIconCache
taskkill /IM explorer.exe /F
start explorer.exe

echo.
echo Build successful! The application is available in the 'dist' folder.
echo.
echo You can find the executable at: dist\SVG_Processor.exe
echo.
echo NOTE: If the icon is still not showing correctly, you may need to restart your computer.
echo.
pause 