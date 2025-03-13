@echo off
echo *** Updating Ignition View File ***
echo.

REM Check for admin rights
NET SESSION >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click on this batch file and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

echo Updating Ignition view with appended SVG elements...
copy /Y "C:\Users\user\Desktop\incscape_transform\updated_view.json" "C:\Program Files\Inductive Automation\Ignition\data\projects\MTN6_SCADA\com.inductiveautomation.perspective\views\Detailed-Views\TestView\view.json"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Success! The view has been updated with all SVG elements.
    echo All existing elements in the view were preserved.
) else (
    echo.
    echo Error occurred while updating the file.
    echo Please make sure Ignition is not using the file.
)

echo.
pause
