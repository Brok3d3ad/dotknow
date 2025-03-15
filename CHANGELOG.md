# SVG Processor Project - Documentation Changelog

## [1.2.3] - 2025-03-18
### Fixed
- Enhanced icon handling with additional debugging information
- Created dedicated build script (build_with_icon.bat) specifically for proper icon embedding
- Added version information metadata to provide better Windows integration
- Added MANIFEST.in file to ensure icon is included in all package distributions
- Improved icon path resolution with multiple fallback options
- Added Windows icon cache clearing to build process
- Added detailed debug logging to icon loading process

## [1.2.2] - 2025-03-17
### Fixed
- Fixed issue with application icon not appearing in the compiled Windows executable
- Added the autStand_ic0n.ico file to the datas section in both spec files to ensure it's properly bundled
- Ensured consistent naming and reference to spec files between build script and actual file names
- Updated README.md with clearer instructions for building with the correct icon

## [1.2.1] - 2025-03-16
### Fixed
- Added missing root element properties in exported view.json files
- Fixed absence of "meta", "props.style", and "type" fields in root element configuration
- Ensured exported views match production SCADA structure for compatibility

## [1.2.0] - 2025-03-15
### Fixed
- Replaced hardcoded values (-7 pixels) in SVG element positioning with half of the user-defined element width and height
- Modified zip export functionality to place files directly in the zip file without an extra folder level

## Project Overview
This project is an SVG to JSON processor tool designed for automation standards. It consists of a GUI application that allows users to:
1. Browse and select SVG files
2. Process SVG files by extracting SVG elements and their attributes
3. Convert these elements into JSON format for use in automation systems
4. Copy results to clipboard or save to file
5. Export to Ignition SCADA project structure as a zip file

## Main Components

### 1. SVG Processor GUI (`svg_processor_gui.py`)
- Tkinter-based graphical user interface
- Handles file selection, configuration, and user interaction
- Displays processing results and output
- Features black and yellow theme with automation standard branding
- Implements SCADA project export functionality

### 2. SVG Transformer (`inkscape_transform.py`)
- Core processing engine that parses SVG files
- Extracts SVG elements (rectangles, circles, ellipses, lines, etc.) and their transformations
- Converts them to the required JSON format
- Handles complex SVG transformations (translate, scale, rotate, matrix)

### 3. Supporting Files
- `requirements.txt`: Lists Python dependencies (numpy, Pillow, pyinstaller)
- `test-requirements.txt`: Lists testing dependencies (pytest, pytest-cov, mock)
- `app_config.json`: Stores application settings and user preferences
- `automation_standard_logo.jpg`: Branding image displayed in the application

## Technology Stack
- Python 3
- Tkinter for GUI
- XML parsing with ElementTree and minidom
- JSON processing
- NumPy for matrix transformations
- PIL/Pillow for image handling
- Pytest for testing

## Edits Log
*This section will be updated after each edit to the project*

### 2024-05-26
- Created initial documentation (CHANGELOG.md and README.md)
- Fixed typo in file references: 'incscape_transform.py' → 'inkscape_transform.py'

### 2024-05-27
- Compiled the application for macOS using PyInstaller
- Created macOS application bundle (`SVG Processor.app`) and standalone executable
- Used macOS-specific settings including bundle identifier

### 2024-05-28
- Fixed tkinter missing module issue in macOS compilation:
  - Installed tcl-tk with Homebrew
  - Installed python-tk@3.11 package
  - Recompiled with explicit tkinter dependencies
  - Added specific tcl/tk libraries to the bundle
- Successfully tested both standalone executable and app bundle
- Updated documentation to include macOS-specific installation notes

### 2024-05-29
- Fixed configuration file path issue:
  - Modified code to create and read config file in executable's directory
  - Added PyInstaller compatibility for both development and bundled modes
  - Updated resource loading paths (logo, icons) to work with bundled app
  - Explicitly bundled resources with the application
- Successfully tested the application to verify it correctly saves and loads configuration 

### 2024-05-30
- Added Ignition SCADA project export functionality:
  - Created new UI section for SCADA project settings
  - Added fields for project title, parent project, view name, and SVG URL
  - Implemented automatic creation of proper folder structure (project/com.inductiveautomation.perspective/views/Detailed-Views/[View Name])
  - Added generation of project.json with configurable title and parent
  - Added generation of standard resource.json
  - Added export functionality for view.json with SVG background and component children
  - Fixed filename inconsistency: created correct 'inkscape_transform.py' file
  - Updated import statement to use properly named module
  - Added configuration persistence for SCADA project settings 

### 2024-05-31
- Enhanced SCADA export configuration options:
  - Added configurable image dimensions (width and height)
  - Added configurable default size for view (width and height)
  - Updated configuration file to include these new settings
  - Modified export functionality to use these customized dimensions 

### 2024-06-01
- Improved Windows compatibility:
  - Enhanced window icon handling for cross-platform support
  - Added Windows-specific PyInstaller spec file for easier compilation
  - Created batch file for one-click Windows builds
  - Updated documentation with Windows-specific troubleshooting information
  - Ensured consistent path handling across platforms 

### 2024-06-02
- Enhanced SCADA project export functionality:
  - Changed export format from folder structure to zip file
  - Added temporary directory handling for building project structure
  - Implemented clean zip file creation with proper relative paths
  - Improved user experience with file save dialog for selecting zip location 

### 2024-06-03
- Repository cleanup:
  - Removed duplicate incorrectly named 'incscape_transform.py' file
  - Ensured consistency by keeping only the correctly named 'inkscape_transform.py'
  - Verified all imports are using the correct file name 

### 2024-06-04
- Enhanced unit testing:
  - Added comprehensive unit tests for SVGTransformer class
  - Created test cases for all SVG element types (rect, circle, ellipse, line, path, etc.)
  - Implemented test fixtures and mock objects for isolated testing
  - Added test coverage for transformation matrix operations
  - Added validation tests for file handling and error cases
  
### 2024-06-05
- Improved SVG parsing functionality:
  - Added support for more SVG element types beyond rectangles
  - Enhanced error handling for malformed SVG files
  - Optimized transformation matrix calculations
  - Added better center point calculation for all element types

### 2024-06-06
- Completed macOS build process:
  - Successfully compiled standalone application for macOS
  - Fixed tkinter-related import issues in bundled application
  - Updated spec file for proper resource inclusion
  - Added detailed instructions for macOS installation requirements

### 2024-06-07
- Updated project documentation:
  - Enhanced README.md with comprehensive testing instructions
  - Updated feature list to include all supported SVG element types
  - Added detailed technical information about matrix transformations
  - Improved project structure documentation
  - Expanded troubleshooting section with platform-specific guidance
  - Added code structure explanations with class relationships 