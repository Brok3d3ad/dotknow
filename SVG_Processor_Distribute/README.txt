# SVG Processor Tool - Executable Release

## Overview
The SVG Processor Tool is an application designed to extract SVG elements from files and convert them to a custom JSON format for use in automation systems. This tool simplifies the process of integrating graphics from vector editing software into automation HMI systems, particularly Ignition SCADA.

## Running the Application
Simply double-click on `SVG_Processor.exe` to launch the application.

## From Different Shells:
- **Windows Explorer:** Simply double-click the `SVG_Processor.exe` file
- **Command Prompt:** Use `SVG_Processor.exe` or the full path
- **PowerShell:** Use `.\SVG_Processor.exe` or the full path
- **Git Bash:** Use one of these approaches:
  - Use the full Windows path: `./SVG_Processor.exe`
  - Use the `start` command: `start SVG_Processor.exe`
  - Use `cmd` to execute it: `cmd //c SVG_Processor.exe`

## Configuration
The application stores its settings in an `app_config.json` file that will be created in the same directory as the executable when you first run the application.

## Features
- User-friendly GUI interface with automation standard branding
- Ability to browse and select SVG files for processing
- Support for multiple SVG element types including rectangles, circles, ellipses, lines, polylines, polygons, paths, and text elements
- Processing of complex SVG transformations including translation, rotation, and scaling
- Conversion of SVG elements to a custom JSON format for automation systems
- Options to copy results to clipboard or save to a file
- Export to Ignition SCADA project structure with proper folder hierarchy and configuration files

## Troubleshooting
If you encounter any issues running the application:
1. Ensure all files (SVG_Processor.exe, automation_standard_logo.jpg, and autStand_ic0n.ico) are in the same directory
2. Try running as Administrator if permission issues occur
3. Make sure your system has the required Visual C++ Redistributable packages installed

For further details or support, please refer to the main project documentation. 