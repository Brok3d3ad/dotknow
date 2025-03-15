# SVG Processor Tool

## Overview
The SVG Processor Tool is an application designed to extract SVG elements from files and convert them to a custom JSON format for use in automation systems. This tool simplifies the process of integrating graphics from vector editing software into automation HMI systems, particularly Ignition SCADA.

## Features
- User-friendly GUI interface with automation standard branding
- Ability to browse and select SVG files for processing
- Support for multiple SVG element types including:
  - Rectangles
  - Circles
  - Ellipses
  - Lines
  - Polylines
  - Polygons
  - Paths
  - Text elements
- Processes complex SVG transformations including translation, rotation, and scaling
- Converts SVG elements to a custom JSON format for automation systems
- Options to copy results to clipboard or save to a file
- Configurable settings for element type and properties path
- Persistent configuration via app_config.json
- Export to Ignition SCADA project structure with proper folder hierarchy and configuration files

## Installation

### Using the Pre-Built Executable (Windows)
The simplest way to use the application is to run the pre-built executable:

1. Navigate to the `SVG_Processor_Distribute` folder in the project directory
2. Double-click on `SVG_Processor.exe` to launch the application

#### Running from different shells:

- **Windows Explorer:** Simply double-click the `SVG_Processor.exe` file
- **Command Prompt:** Use `SVG_Processor.exe` or the full path
- **PowerShell:** Use `.\SVG_Processor.exe` or the full path
- **Git Bash:** Git Bash doesn't directly execute Windows `.exe` files by name. Use one of these approaches:
  - Use the full Windows path: `./SVG_Processor.exe`
  - Use the `start` command: `start SVG_Processor.exe`
  - Use `cmd` to execute it: `cmd //c SVG_Processor.exe`

> **Note:** If you encounter the "command not found" error in Git Bash, it's because Git Bash uses a Unix-like environment that doesn't automatically recognize Windows executables. Use one of the methods listed above instead.

### Prerequisites
- Python 3.6 or higher (only needed if building from source)
- Required Python packages (listed in requirements.txt):
  - numpy>=1.21.0
  - Pillow>=9.0.0
  - pyinstaller>=6.0.0 (for building standalone executables)
- tkinter (for the GUI interface)

### Setup
1. Clone or download this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. For development and testing, also install test dependencies:
   ```
   pip install -r test-requirements.txt
   ```
4. Run the application:
   ```
   python svg_processor_gui.py
   ```

### Building a Standalone Executable

#### For Windows

To build the application on Windows, use PyInstaller directly:

**Option 1: One-step build with all options (Recommended)**
```
pyinstaller --onefile --windowed --name="SVG_Processor" --icon=autStand_ic0n.ico --add-data="automation_standard_logo.jpg;." --add-data="autStand_ic0n.ico;." --hidden-import=numpy --hidden-import=PIL --hidden-import=PIL._tkinter_finder svg_processor_gui.py
```

This command:
- Creates a single-file executable (`--onefile`)
- Makes it a windowed application without console (`--windowed`)
- Names the output executable "SVG_Processor" (`--name`)
- Uses the custom icon file (`--icon`)
- Includes necessary resources (`--add-data`)
- Ensures all dependencies are bundled (`--hidden-import`)

**Option 2: Using the spec file**
```
pyinstaller autStand_icon.spec
```

The spec file includes all the necessary configuration for building with the correct icon and dependencies.

> **Note on Windows Icon Issues**: If the application icon is not appearing correctly:
> 1. Make sure the `autStand_ic0n.ico` file is present in your project directory
> 2. Try refreshing the Windows icon cache with: `ie4uinit.exe -ClearIconCache`
> 3. In persistent cases, you may need to restart your computer to clear the Windows icon cache completely

The compiled executable will be created in the `dist` folder.

#### For macOS

##### Install Required Dependencies
For macOS, you need to ensure tkinter and other dependencies are properly installed:

```bash
# Install Tcl/Tk framework
brew install tcl-tk

# Install Python with tkinter support
brew install python-tk@3.11

# Install required Python packages
pip install numpy Pillow pyinstaller
```

##### Compile the Application
```bash
pyinstaller --clean --onefile --windowed --name="SVG_Processor" \
  --osx-bundle-identifier="com.automationstandard.svgprocessor" \
  --hidden-import=numpy --hidden-import=PIL --hidden-import=PIL._tkinter_finder \
  --hidden-import=tkinter --hidden-import=_tkinter \
  --hidden-import=tkinter.filedialog --hidden-import=tkinter.messagebox \
  --hidden-import=tkinter.scrolledtext --hidden-import=tkinter.ttk \
  --collect-data=tkinter \
  --add-data="/opt/homebrew/Cellar/tcl-tk@8/8.6.16/lib/tcl8.6:tcl8.6" \
  --add-data="/opt/homebrew/Cellar/tcl-tk@8/8.6.16/lib/tk8.6:tk8.6" \
  --add-data="automation_standard_logo.jpg:." \
  --add-data="autStand_ic0n.ico:." \
  --icon=autStand_ic0n.ico svg_processor_gui.py
```

Note: Your Tcl/Tk path may be different. Check with `brew info tcl-tk` to find the correct path.

The macOS build will create:
- `SVG_Processor.app` - A macOS application bundle that can be dragged to Applications
- `SVG_Processor` - A standalone executable

#### For Linux

##### Install Required Dependencies
```bash
# Install required system packages
sudo apt-get install python3-tk python3-dev

# Install required Python packages
pip install numpy Pillow pyinstaller
```

##### Compile the Application
```bash
pyinstaller --clean --onefile --windowed --name="SVG_Processor" \
  --hidden-import=numpy --hidden-import=PIL --hidden-import=PIL._tkinter_finder \
  --add-data="automation_standard_logo.jpg:." \
  --add-data="autStand_ic0n.ico:." \
  --icon=autStand_ic0n.ico svg_processor_gui.py
```

The Linux build will create:
- `SVG_Processor` - A standalone executable in the `dist` folder

## Usage
1. Launch the application
2. Click "Browse" to select an SVG file
3. Configure the settings if needed:
   - Element Type: Type of element to create in the target system
   - Properties Path: Path in the properties tree
   - Element Width/Height: Default dimensions for elements
4. Click "Process SVG" to extract and convert SVG elements
5. View the results in the output area
6. Use "Copy to Clipboard" or "Save to File" to export the JSON results
7. Export to Ignition SCADA project by configuring:
   - Project Title: Name of the SCADA project
   - Parent Project: Parent project reference
   - View Name: Name of the view to create
   - SVG URL: URL to the SVG file (typically a local server URL)
   - Image Dimensions: Width and height of the SVG background image
   - Default Size: Width and height of the view container
8. Click "Export SCADA Project" to create the complete project structure as a zip file

## Configuration
The application stores its settings in an `app_config.json` file located in the same directory as the executable. This file contains:

- Last used file path
- Element type setting
- Properties path setting
- Element width and height settings
- SCADA project settings:
  - Project title and parent project
  - View name and SVG URL
  - Image dimensions (width and height)
  - Default size dimensions (width and height)

The configuration is automatically saved when you exit the application and loaded when you start it again. If the configuration file doesn't exist, a default one will be created.

## Testing

The project includes a comprehensive test suite to ensure stability and correctness:

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_inkscape_transform.py
```

### Test Suite Components
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interaction between components
- **Mock Tests**: Use mock objects to simulate external dependencies
- **Transformation Tests**: Verify matrix operations and SVG transformations

### Test Coverage
The test suite aims to provide high coverage of the codebase, with particular focus on:
- SVG parsing and transformation logic
- Element type handling (rect, circle, ellipse, etc.)
- Error cases and edge conditions
- Configuration management

## Troubleshooting

### Windows-Specific Issues

1. **Missing dependencies error**:
   If you see errors related to missing DLLs or modules, try installing the Visual C++ Redistributable:
   ```
   Download and install the latest Visual C++ Redistributable from Microsoft's website
   ```

2. **Tkinter issues**:
   If the application crashes with tkinter-related errors:
   ```
   Make sure Python is installed with tcl/tk support
   Try reinstalling Python with the "tcl/tk and IDLE" option checked
   ```

3. **Icon not displaying**:
   If the application icon is not showing:
   ```
   Make sure automation_standard_logo.jpg is included in the same directory as the exe
   ```

### macOS Tkinter Issues
If you encounter `ModuleNotFoundError: No module named 'tkinter'` when running the compiled app:

1. Ensure you have Tcl/Tk installed:
   ```
   brew install tcl-tk
   ```

2. Install the Python Tkinter binding:
   ```
   brew install python-tk@3.11
   ```

3. Recompile with the extended PyInstaller command shown in the "For macOS" section above.

### General Troubleshooting
- If the application crashes or doesn't start, try running it from the command line to see error messages
- Check that all dependencies are installed correctly
- Ensure the SVG files you're processing are valid and accessible
- If the application can't find its configuration file, check the permissions of the directory where the app is located

## Technical Details

### Core Components
- **SVGProcessorApp**: The main GUI application class that provides the user interface
  - Handles file selection, configuration, and user interaction
  - Manages application state and configuration persistence
  - Implements SCADA project export functionality
  
- **SVGTransformer**: Core processing engine that handles SVG parsing and transformation
  - Parses SVG files using XML DOM
  - Implements matrix transformation operations
  - Processes different element types with specialized handlers
  - Calculates correct positions accounting for transformations

- **ConfigManager**: Handles saving and loading of user preferences
  - Manages `app_config.json` file
  - Provides default configurations when needed
  - Handles path resolution for both development and bundled mode

### SVG Processing Flow
1. SVG file is loaded and parsed using XML DOM
2. Elements are identified and classified by type (rect, circle, ellipse, etc.)
3. Each element's original position, size, and attributes are extracted
4. Complex transformations are calculated using matrix operations:
   - Matrix: Direct transformation using a 3x3 matrix
   - Translate: Moving elements by x,y offsets
   - Scale: Resizing elements by x,y factors
   - Rotate: Rotating elements around a specified point
5. Elements are converted to the required JSON format
6. Results are displayed and can be exported

### Matrix Transformation
The application uses 3x3 transformation matrices in homogeneous coordinates:
- Identity matrix: No transformation
- Translation matrix: [1,0,tx; 0,1,ty; 0,0,1]
- Rotation matrix: [cos(a),-sin(a),0; sin(a),cos(a),0; 0,0,1]
- Scale matrix: [sx,0,0; 0,sy,0; 0,0,1]

Multiple transformations are combined by matrix multiplication.

## Project Structure
- `svg_processor_gui.py`: Main application with GUI implementation
- `inkscape_transform.py`: SVG processing engine
- `app_config.json`: Application configuration file
- `requirements.txt`: Python dependencies
- `test-requirements.txt`: Testing dependencies
- `tests/`: Test suite directory
  - `test_inkscape_transform.py`: Tests for the SVG transformer
  - `test_svg_processor_gui.py`: Tests for the GUI application
- `automation_standard_logo.jpg`: Application logo

## SCADA Project Export
The application can generate a complete Ignition SCADA project structure as a zip file with:

1. Proper folder hierarchy inside the zip:
   ```
   [Project Name]_[Date]_[Time]/
   ├── project.json
   └── com.inductiveautomation.perspective/
       └── views/
           └── Detailed-Views/
               └── [View Name]/
                   ├── view.json
                   ├── thumbnail.png
                   └── resource.json
   ```

2. Correctly configured JSON files:
   - project.json: Contains project title and parent reference
   - resource.json: Standard resource configuration
   - view.json: Complete view with SVG background and component children

3. All SVG elements are properly formatted as SCADA components with:
   - Correct positioning and dimensions
   - Proper component type and path
   - Tag property configuration
   - Rotation if applicable

4. Export workflow:
   - Configure export settings
   - Click "Export SCADA Project"
   - Choose where to save the zip file
   - The temporary folder structure is automatically created and zipped

## License
[Your License Information]

## Acknowledgments
- Built for automation standard systems
- Uses open-source Python libraries for XML processing and GUI 