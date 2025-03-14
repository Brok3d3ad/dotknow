# SVG Processor Tool

## Overview
The SVG Processor Tool is an application designed to extract rectangle elements from SVG files and convert them to a custom JSON format for use in automation systems. This tool simplifies the process of integrating graphics from vector editing software into automation HMI systems.

## Features
- User-friendly GUI interface with automation standard branding
- Ability to browse and select SVG files for processing
- Extracts rectangle elements with their positions, sizes, and attributes
- Processes complex SVG transformations including translation, rotation, and scaling
- Converts SVG elements to a custom JSON format for automation systems
- Options to copy results to clipboard or save to a file
- Configurable settings for element type and properties path
- Persistent configuration via app_config.json

## Installation

### Prerequisites
- Python 3.6 or higher
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
3. Run the application:
   ```
   python svg_processor_gui.py
   ```

### Building a Standalone Executable

#### For Windows
```
pyinstaller --onefile --windowed --icon=automation_standard_logo.jpg --add-data="automation_standard_logo.jpg;." svg_processor_gui.py
```

#### For macOS

##### Install Required Dependencies
For macOS, you need to ensure tkinter is properly installed:

```bash
# Install Tcl/Tk framework
brew install tcl-tk

# Install Python with tkinter support
brew install python-tk@3.11
```

##### Compile the Application
```bash
pyinstaller --clean --onefile --windowed --name="SVG Processor" \
  --osx-bundle-identifier="com.automationstandard.svgprocessor" \
  --hidden-import=tkinter --hidden-import=_tkinter \
  --hidden-import=tkinter.filedialog --hidden-import=tkinter.messagebox \
  --hidden-import=tkinter.scrolledtext --hidden-import=tkinter.ttk \
  --collect-data=tkinter \
  --add-data="/opt/homebrew/Cellar/tcl-tk@8/8.6.16/lib/tcl8.6:tcl8.6" \
  --add-data="/opt/homebrew/Cellar/tcl-tk@8/8.6.16/lib/tk8.6:tk8.6" \
  --add-data="automation_standard_logo.jpg:." \
  --icon=automation_standard_logo.jpg svg_processor_gui.py
```

Note: Your Tcl/Tk path may be different. Check with `brew info tcl-tk@8` to find the correct path.

The macOS build will create:
- `SVG Processor.app` - A macOS application bundle that can be dragged to Applications
- `SVG Processor` - A standalone executable

#### For Linux
```
pyinstaller --onefile --windowed --add-data="automation_standard_logo.jpg:." svg_processor_gui.py
```

## Usage
1. Launch the application
2. Click "Browse" to select an SVG file
3. Configure the settings if needed:
   - Element Type: Type of element to create in the target system
   - Properties Path: Path in the properties tree
   - Element Width/Height: Default dimensions for elements
4. Click "Process SVG" to extract and convert rectangle elements
5. View the results in the output area
6. Use "Copy to Clipboard" or "Save to File" to export the JSON results

## Configuration
The application stores its settings in an `app_config.json` file located in the same directory as the executable. This file contains:

- Last used file path
- Element type setting
- Properties path setting
- Element width and height settings

The configuration is automatically saved when you exit the application and loaded when you start it again. If the configuration file doesn't exist, a default one will be created.

## Troubleshooting

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
- **SVGTransformer**: Core processing engine that handles SVG parsing and transformation
- **Configuration Management**: Handles saving and loading of user preferences

### SVG Processing Flow
1. SVG file is loaded and parsed using XML DOM
2. Rectangle elements are extracted from the SVG
3. Transformations are applied to determine final positions
4. Elements are converted to the required JSON format
5. Results are displayed and can be exported

## Project Structure
- `svg_processor_gui.py`: Main application with GUI implementation
- `inkscape_transform.py`: SVG processing engine
- `app_config.json`: Application configuration file
- `requirements.txt`: Python dependencies
- `automation_standard_logo.jpg`: Application logo

## License
[Your License Information]

## Acknowledgments
- Built for automation standard systems
- Uses open-source Python libraries for XML processing and GUI 