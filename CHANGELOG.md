# SVG Processor Project - Documentation Changelog

## Project Overview
This project is an SVG to JSON processor tool designed for automation standards. It consists of a GUI application that allows users to:
1. Browse and select SVG files
2. Process SVG files by extracting rectangle elements and their attributes
3. Convert these elements into JSON format for use in automation systems
4. Copy results to clipboard or save to file

## Main Components

### 1. SVG Processor GUI (`svg_processor_gui.py`)
- Tkinter-based graphical user interface
- Handles file selection, configuration, and user interaction
- Displays processing results and output
- Features black and yellow theme with automation standard branding

### 2. SVG Transformer (`inkscape_transform.py`)
- Core processing engine that parses SVG files
- Extracts rectangle elements and their transformations
- Converts them to the required JSON format
- Handles complex SVG transformations (translate, scale, rotate, matrix)

### 3. Supporting Files
- `requirements.txt`: Lists Python dependencies (numpy, Pillow, pyinstaller)
- `app_config.json`: Stores application settings and user preferences
- `automation_standard_logo.jpg`: Branding image displayed in the application

## Technology Stack
- Python 3
- Tkinter for GUI
- XML parsing with ElementTree and minidom
- JSON processing
- NumPy for matrix transformations
- PIL/Pillow for image handling

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