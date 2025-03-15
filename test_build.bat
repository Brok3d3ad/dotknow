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

REM Install virtualenv if needed
echo Installing/upgrading virtualenv...
python -m pip install --upgrade virtualenv
if %errorlevel% neq 0 (
    echo Failed to install virtualenv.
    pause
    exit /b 1
)

REM Setup virtual environment with absolute paths
echo Setting up virtual environment...
set "VENV_DIR=%CURRENT_DIR%\test_venv"
if exist "%VENV_DIR%" (
    echo Test virtual environment already exists, removing old one...
    rmdir /s /q "%VENV_DIR%"
)

REM Create virtual environment using virtualenv
echo Creating test virtual environment in: %VENV_DIR%
python -m virtualenv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo Failed to create test virtual environment.
    pause
    exit /b 1
)

REM Check if we can find the activation script
echo Checking activation script...
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Found Windows activation script.
    set "ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat"
) else if exist "%VENV_DIR%\bin\activate" (
    echo Found Unix activation script.
    set "ACTIVATE_SCRIPT=%VENV_DIR%\bin\activate"
) else (
    echo No activation script found. Listing virtual environment directory:
    dir "%VENV_DIR%"
    if exist "%VENV_DIR%\Scripts" echo Listing Scripts directory: & dir "%VENV_DIR%\Scripts"
    if exist "%VENV_DIR%\bin" echo Listing bin directory: & dir "%VENV_DIR%\bin"
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating test virtual environment using: %ACTIVATE_SCRIPT%
call "%ACTIVATE_SCRIPT%"
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Verify virtual environment is activated
echo Checking Python executable after activation:
where python
python -c "import sys; print('Python path:', sys.executable)"

REM Install required packages
echo Installing required packages...
python -m pip install -r "%CURRENT_DIR%\requirements.txt"
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

REM Ensure numpy is installed
echo Ensuring numpy is installed...
python -m pip install numpy
if %errorlevel% neq 0 (
    echo Failed to install numpy.
    pause
    exit /b 1
)

REM Create temp build directory
set "TEST_BUILD_DIR=%CURRENT_DIR%\test_build"
if exist "%TEST_BUILD_DIR%" rmdir /s /q "%TEST_BUILD_DIR%"
mkdir "%TEST_BUILD_DIR%"

echo.
echo Testing compilation using PyInstaller...
python -m PyInstaller --workpath="%TEST_BUILD_DIR%\build" --distpath="%TEST_BUILD_DIR%\dist" --specpath="%TEST_BUILD_DIR%" --clean "%CURRENT_DIR%\autStand_icon.spec"

if %errorlevel% neq 0 (
    echo Build test failed!
    pause
    exit /b 1
)

echo.
echo Build test successful! Compilation works correctly.
echo.

REM Clean up test environment
echo Cleaning up test environment...
rmdir /s /q "%VENV_DIR%"
rmdir /s /q "%TEST_BUILD_DIR%"

echo.
echo Test complete. You can now safely commit and push your changes.
echo.

pause 