@echo off
echo Building SVG Processor with custom icon...
echo.

REM Get the current directory
set "CURRENT_DIR=%CD%"
echo Current working directory: %CURRENT_DIR%

REM Check Python availability and version
echo Checking Python installation...
where python
if %errorlevel% neq 0 (
    echo Python not found in PATH. Please install Python or add it to your PATH.
    pause
    exit /b 1
)
python --version

REM Setup virtual environment with absolute paths
echo Setting up virtual environment...
set "VENV_DIR=%CURRENT_DIR%\venv"
if exist "%VENV_DIR%" (
    echo Virtual environment already exists, removing old one...
    rmdir /s /q "%VENV_DIR%"
)

REM Create virtual environment
echo Creating virtual environment in: %VENV_DIR%
python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

REM Activate virtual environment - use full path to activate script
echo Activating virtual environment...
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo Activation script not found at: %VENV_DIR%\Scripts\activate.bat
    echo Listing Scripts directory content:
    dir "%VENV_DIR%\Scripts"
    pause
    exit /b 1
)

REM Verify virtual environment is activated
echo Checking Python executable after activation:
where python
python -c "import sys; print('Python path:', sys.executable)"

REM Check if PyInstaller is installed in the virtual environment
echo Checking for PyInstaller...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing required packages...
    pip install -r "%CURRENT_DIR%\requirements.txt"
    if %errorlevel% neq 0 (
        echo Failed to install requirements.
        call "%VENV_DIR%\Scripts\deactivate.bat"
        pause
        exit /b 1
    )
)

REM Ensure numpy is installed
echo Ensuring numpy is installed...
pip install numpy
if %errorlevel% neq 0 (
    echo Failed to install numpy.
    call "%VENV_DIR%\Scripts\deactivate.bat"
    pause
    exit /b 1
)

REM Remove any existing build and dist folders to ensure clean build
echo Cleaning previous builds...
if exist "%CURRENT_DIR%\build" rmdir /s /q "%CURRENT_DIR%\build"
if exist "%CURRENT_DIR%\dist" rmdir /s /q "%CURRENT_DIR%\dist"

echo.
echo Building application using PyInstaller with custom icon...
pyinstaller "%CURRENT_DIR%\autStand_icon.spec"

if %errorlevel% neq 0 (
    echo Build failed!
    call "%VENV_DIR%\Scripts\deactivate.bat"
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
echo You can find the executable at: %CURRENT_DIR%\dist\SVG_Processor.exe
echo.
echo NOTE: If the icon is still not showing correctly, you may need to restart your computer.
echo.

REM Deactivate the virtual environment
call "%VENV_DIR%\Scripts\deactivate.bat"
echo Virtual environment deactivated.
echo.

pause 