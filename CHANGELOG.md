# SVG Processor - Changelog

## Recent Updates

### [1.12.0] - 2025-04-05
- Added new "Final Prefix" and "Final Suffix" fields for element mappings to handle potential typos
- Enhanced prefix and suffix handling to automatically add underscores when needed 
  - Final prefixes are automatically followed by "_" if not already present
  - Final suffixes are automatically preceded by "_" if not already present
- Fixed layout issues with element mapping table
- Fixed bug with delete mapping button functionality
- Increased default application window size to 1200x800 for better usability
- Expanded width of Properties Path input field to 50 characters for better visibility
- Expanded width of Final Prefix and Final Suffix input fields to 15 characters
- Fixed element reindexing after row removal

### [1.11.0] - 2025-04-03
- Added support for negative offset values for precise positioning of elements
- Enhanced path element handling with accurate coordinate extraction
- Fixed regex pattern for correctly parsing comma-separated and space-separated coordinates in SVG paths
- Improved suffix-based rotation override system with clearer debug output
- Added proper y-coordinate handling for SVG path elements
- Enhanced debugging output for better troubleshooting
- Fixed issue where paths properties were not being correctly applied
- Improved element property path handling based on element mappings

### [1.10.1] - 2025-04-02
- Improved rotation handling for SVG elements with transform attributes
- Enhanced rotation angle extraction from SVG transforms
- Added better debugging for rotation transformations
- Fixed direct rotation extraction from transform strings
- Added matrix-based rotation calculation as fallback method

### [1.10.0] - 2025-04-01
- Improved test coverage to over 80% for all core components
- Enhanced test suite to verify all element types and transformations
- Fixed configuration persistence issues across application restarts
- Optimized matrix transformation operations for better performance

### [1.9.5] - 2025-03-31
- Implemented priority-based element type mapping system
- Added support for label prefix-based element configurations
- Ensured correct handling of empty label prefix mappings as fallback
- Fixed issues with configuration settings not being preserved correctly
- Improved handling of SVG element properties based on label prefixes

### [1.9.0] - 2025-03-31
- Removed global Element Type and Properties Path fields in favor of per-element settings
- Streamlined user interface by eliminating redundant global fields
- Enhanced configuration validation for element mappings
- Improved element mapping handling for better flexibility

### [1.8.0] - 2025-03-30
- Added per-element Properties Path and Size settings in Element Mapping tab
- Each SVG element type can now have its own Properties Path and Size (width/height) 
- Removed global Element Size setting for more flexibility
- Improved configuration persistence for element-specific settings
- Enhanced user interface with compact width × height inputs

### [1.7.0] - 2025-03-29
- Redesigned Element Mapping tab with dynamic add/remove functionality
- Removed fixed element labels to allow complete user customization
- Added remove buttons for each element mapping
- Enhanced UI to support unlimited custom element mappings
- Improved usability for managing SVG element type mappings

### [1.6.0] - 2025-03-28
- Added editable SVG element type fields allowing direct customization of SVG element representations
- Enhanced Element Mapping tab to support dynamic addition of custom element mappings
- Improved configuration persistence for custom SVG element types
- Updated UI to provide better guidance on SVG element type customization

### [1.5.0] - 2025-03-27
- Added support for user-defined custom SVG element representations
- Enhanced Element Mapping tab to allow adding custom SVG element types
- Persistent storage of custom element mappings in configuration
- Improved UI for managing element type mappings

### [1.4.1] - 2025-03-26
- Enhanced code organization and structure
- Improved error handling for SVG transformation operations
- Optimized performance for complex SVG elements
- Fixed minor UI responsiveness issues

### [1.4.0] - 2025-03-25
- Added support for processing multiple SVG element types beyond rectangles
- Added element type mapping to allow different element types for different SVG elements
- Created new Element Mapping tab in the GUI for configuring element type mappings
- Enhanced SVG transformation code to handle circles, ellipses, lines, polylines, polygons, and paths

### [1.3.1] - 2025-03-24
- Created SVG_Processor_Distribute folder with compiled Windows executable
- Updated documentation for running pre-built executable

### [1.3.0] - 2025-03-23
- Simplified build process with direct PyInstaller commands
- Standardized executable naming across platforms

### [1.2.7] - 2025-03-22
- Enhanced cross-platform virtual environment handling
- Improved Python path handling

### [1.2.6] - 2025-03-21
- Fixed build script and path handling issues
- Added validation for Python environment

### [1.2.5] - 2025-03-20
- Added virtual environment support for isolated dependency installation

### [1.2.4] - 2025-03-19
- Fixed "No module named 'numpy'" error in compiled executable

### [1.2.3] - 2025-03-18
- Enhanced icon handling with better debugging and fallbacks

### [1.2.2] - 2025-03-17
- Fixed Windows executable icon bundling issues

### [1.2.1] - 2025-03-16
- Fixed missing root element properties in exported view.json files

### [1.2.0] - 2025-03-15
- Replaced hardcoded position values with dynamic calculations
- Improved zip export structure

## Project Overview
An SVG to JSON processor tool for automation standards that:
1. Processes SVG files by extracting elements and attributes
2. Converts elements to JSON format for automation systems
3. Exports to Ignition SCADA project structure as zip files

## Main Components

### 1. SVG Processor GUI (`svg_processor_gui.py`)
- Tkinter GUI for file handling, configuration, and user interaction
- SCADA project export functionality
- Black and yellow theme with automation standard branding

### 2. SVG Transformer (`inkscape_transform.py`)
- Parses SVG files and extracts elements
- Handles complex SVG transformations (translate, scale, rotate, matrix)
- Converts to required JSON format

### 3. Supporting Files
- `requirements.txt`: Python dependencies
- `app_config.json`: Application settings
- `automation_standard_logo.jpg`: Branding image

## Technology Stack
- Python 3, Tkinter, XML parsing
- JSON processing, NumPy, PIL/Pillow
- PyInstaller for packaging

## Development History

### 2024-06-07
- Enhanced documentation with testing instructions and technical details

### 2024-06-06
- Completed macOS build process with tkinter fixes

### 2024-06-05
- Added support for more SVG element types
- Optimized transformation calculations

### 2024-06-04
- Added comprehensive unit tests for all components

### 2024-06-03
- Fixed file naming consistency

### 2024-06-02
- Enhanced SCADA export with zip file packaging

### 2024-06-01
- Improved cross-platform compatibility

### 2024-05-31
- Added configurable dimensions for SCADA views

### 2024-05-30
- Added Ignition SCADA project export functionality

### 2024-05-29
- Fixed configuration and resource path handling

### 2024-05-28
- Fixed macOS-specific module issues

### 2024-05-27
- Added macOS compilation support

### 2024-05-26
- Initial documentation and file structure 