@echo off
echo Building SVG Processor for Windows...
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

echo.
echo Building application using PyInstaller...
pyinstaller SVG_Processor_Windows.spec

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful! The application is available in the 'dist' folder.
echo.
echo You can find the executable at: dist\SVG Processor.exe
echo.
pause 