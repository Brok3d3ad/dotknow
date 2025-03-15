@echo off
echo Testing SVG Processor build...
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
set "VENV_DIR=%CURRENT_DIR%\test_venv"
if exist "%VENV_DIR%" (
    echo Test virtual environment already exists, removing old one...
    rmdir /s /q "%VENV_DIR%"
)

REM Create virtual environment
echo Creating test virtual environment in: %VENV_DIR%
python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo Failed to create test virtual environment.
    pause
    exit /b 1
)

REM Activate virtual environment - use full path to activate script
echo Activating test virtual environment...
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

REM Install required packages
echo Installing required packages...
pip install -r "%CURRENT_DIR%\requirements.txt"
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    call "%VENV_DIR%\Scripts\deactivate.bat"
    rmdir /s /q "%VENV_DIR%"
    pause
    exit /b 1
)

REM Ensure numpy is installed
echo Ensuring numpy is installed...
pip install numpy
if %errorlevel% neq 0 (
    echo Failed to install numpy.
    call "%VENV_DIR%\Scripts\deactivate.bat"
    rmdir /s /q "%VENV_DIR%"
    pause
    exit /b 1
)

REM Create temp build directory
set "TEST_BUILD_DIR=%CURRENT_DIR%\test_build"
if exist "%TEST_BUILD_DIR%" rmdir /s /q "%TEST_BUILD_DIR%"
mkdir "%TEST_BUILD_DIR%"

echo.
echo Testing compilation using PyInstaller...
pyinstaller --workpath="%TEST_BUILD_DIR%\build" --distpath="%TEST_BUILD_DIR%\dist" --specpath="%TEST_BUILD_DIR%" --clean "%CURRENT_DIR%\autStand_icon.spec"

if %errorlevel% neq 0 (
    echo Build test failed!
    call "%VENV_DIR%\Scripts\deactivate.bat"
    rmdir /s /q "%VENV_DIR%"
    rmdir /s /q "%TEST_BUILD_DIR%"
    pause
    exit /b 1
)

echo.
echo Build test successful! Compilation works correctly.
echo.

REM Clean up test environment
echo Cleaning up test environment...
call "%VENV_DIR%\Scripts\deactivate.bat"
rmdir /s /q "%VENV_DIR%"
rmdir /s /q "%TEST_BUILD_DIR%"

echo.
echo Test complete. You can now safely commit and push your changes.
echo.

pause 