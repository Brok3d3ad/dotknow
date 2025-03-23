# SVG Processor Tool

## Overview
An application for extracting SVG elements and converting them to JSON format for automation systems, particularly Ignition SCADA.

## Features
- GUI with automation standard branding
- Supports multiple SVG element types (rectangles, circles, ellipses, lines, polylines, polygons, paths)
- Handles complex SVG transformations (translation, rotation, scaling)
- Enhanced rotation handling with direct extraction and matrix-based calculations
- Optimized performance for processing complex SVG elements
- Enhanced error handling for reliable operation
- Supports custom SVG element representations and mappings
- **Label prefix-based element configurations**
- **Final prefix and suffix fields for consistent element naming**
- **Automatic underscore handling for prefixes and suffixes**
- **Consistent configuration management with improved persistence**
- **High test coverage (>80%) for reliable code base**
- **Enhanced path element handling with precise coordinate extraction**
- **Support for negative offset values for precise positioning**
- **Suffix-based rotation override system (r, d, l, u suffixes)**
- **Robust export handling and error recovery for SCADA projects**
- Converts elements to custom JSON format
- Clipboard/file export options
- Configurable element settings
- Persistent configuration
- Ignition SCADA project export with proper structure

## Installation

### Quick Start (Windows)
1. Navigate to `SVG_Processor_Distribute` folder
2. Run `SVG_Processor.exe`

#### Shell Commands
- **Windows Explorer:** Double-click the exe
- **Command Prompt:** `SVG_Processor.exe`
- **PowerShell:** `.\SVG_Processor.exe`
- **Git Bash:** `./SVG_Processor.exe` or `start SVG_Processor.exe`

### Prerequisites
- Python 3.6+ (for building from source)
- Required packages: numpy, Pillow, pyinstaller
- tkinter for GUI

### Building from Source
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python svg_processor_gui.py`

### Build Commands

#### Windows
```
pyinstaller --onefile --windowed --name="SVG_Processor" --icon=autStand_ic0n.ico --add-data="automation_standard_logo.jpg;." --add-data="autStand_ic0n.ico;." --hidden-import=numpy --hidden-import=PIL --hidden-import=PIL._tkinter_finder svg_processor_gui.py
```

#### macOS
```bash
# Install dependencies
brew install tcl-tk python-tk@3.11
pip install numpy Pillow pyinstaller

# Build
pyinstaller --clean --onefile --windowed --name="SVG_Processor" \
  --osx-bundle-identifier="com.automationstandard.svgprocessor" \
  --hidden-import=numpy --hidden-import=PIL --hidden-import=PIL._tkinter_finder \
  --hidden-import=tkinter --collect-data=tkinter \
  --add-data="automation_standard_logo.jpg:." --add-data="autStand_ic0n.ico:." \
  --icon=autStand_ic0n.ico svg_processor_gui.py
```

#### Linux
```bash
# Dependencies
sudo apt-get install python3-tk python3-dev
pip install numpy Pillow pyinstaller

# Build
pyinstaller --clean --onefile --windowed --name="SVG_Processor" \
  --hidden-import=numpy --hidden-import=PIL \
  --add-data="automation_standard_logo.jpg:." --add-data="autStand_ic0n.ico:." \
  --icon=autStand_ic0n.ico svg_processor_gui.py
```

## Usage
1. Launch application
2. Browse for SVG file
3. Configure settings:
   - **Element Mappings tab**:
     - Configure element type, properties path, and size for different SVG elements
     - Use label prefix mappings for specialized element configurations
     - Set final prefix/suffix values to be applied to element names
     - Customize SVG element behavior based on element labels
4. Process SVG
5. Copy/save results
6. For SCADA export, configure:
   - Project Title, Parent Project, View Name, SVG URL
   - Image and View Dimensions
7. Export SCADA project as zip

## Configuration
Settings stored in `app_config.json`:
- File paths
- Element settings with label prefix mappings
- SCADA project configuration
- UI preferences

## Testing
```bash
# Run tests
pytest
# With coverage
pytest --cov=. --cov-report=term-missing
```

## Troubleshooting

### Windows
- **Missing dependencies:** Install Visual C++ Redistributable
- **Tkinter issues:** Ensure Python has tcl/tk support
- **Icon problems:** Check resource files and refresh icon cache

### macOS
- **Tkinter missing:** Install dependencies with `brew install tcl-tk python-tk@3.11`

### General
- Run from command line to see error messages
- Verify dependencies and file permissions
- Ensure SVG files are valid

## Technical Details

### Components
- **SVGProcessorApp:** GUI interface and configuration
- **SVGTransformer:** Parsing and transformation engine
- **ConfigManager:** Configuration handler

### SVG Processing
1. Parse SVG with XML DOM
2. Identify elements by type
3. Extract position, size, attributes
4. Apply matrix transformations
5. Convert to JSON format

### Label Prefix System
- Configure element behavior based on element label prefixes
- Specialized mappings for elements with specific prefixes
- Default mappings for elements without prefixes
- Priority-based mapping selection (exact match > fallback)
- Final prefix and suffix options for consistent element naming
  - Final prefixes automatically add underscore separator (_) if not included
  - Final suffixes automatically add underscore separator (_) if not included

### Performance Optimizations
- Efficient matrix operations for faster transformation calculations
- Optimized element processing for complex SVG files
- Memory usage improvements for large SVG documents

### Error Handling
- Graceful recovery from malformed SVG elements
- Detailed error reporting in the application log
- Validation of user input and configuration parameters

### Matrix Transformations
Uses 3x3 homogeneous coordinate matrices for:
- Translation: [1,0,tx; 0,1,ty; 0,0,1]
- Rotation: [cos(a),-sin(a),0; sin(a),cos(a),0; 0,0,1]
- Scale: [sx,0,0; 0,sy,0; 0,0,1]

### Rotation Handling
- Direct extraction of rotation angles from SVG transform strings
- Handles rotation around origin: rotate(angle)
- Supports rotation around specific points: rotate(angle cx cy)
- Fallback to matrix-based rotation calculation using arctan2
- Preserves rotation information in exported JSON for SCADA systems

## SCADA Export Structure
```
[Project Name]/
├── project.json
└── com.inductiveautomation.perspective/
    └── views/
        └── Detailed-Views/
            └── [View Name]/
                ├── view.json
                ├── thumbnail.png
                └── resource.json
```

Elements exported as SCADA components with proper positioning, type, path, and tag configuration.

## License
[Your License Information]

## Acknowledgments
- Built for automation standard systems
- Uses open-source Python libraries for XML processing and GUI 