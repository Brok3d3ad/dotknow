# SVG Processor Tool v1.10.1

## Installation
1. Extract all files to a folder on your computer
2. Run SVG_Processor.exe
3. No additional installation required

## New in Version 1.10.1
- Improved rotation handling for SVG elements with transform attributes
- Enhanced rotation angle extraction from SVG transforms
- Added better debugging for rotation transformations
- Fixed direct rotation extraction from transform strings
- Added matrix-based rotation calculation as fallback method

## Features
- GUI with automation standard branding
- Supports multiple SVG element types (rectangles, circles, ellipses, lines, polylines, polygons, paths, text)
- Handles complex SVG transformations (translation, rotation, scaling)
- Enhanced rotation handling with direct extraction and matrix-based calculations
- Optimized performance for processing complex SVG elements
- Enhanced error handling for reliable operation
- Supports custom SVG element representations and mappings
- Label prefix-based element configurations
- Consistent configuration management with improved persistence
- Converts elements to custom JSON format
- Clipboard/file export options
- Configurable element settings
- Persistent configuration
- Ignition SCADA project export with proper structure

## Usage
1. Launch application
2. Browse for SVG file
3. Configure settings:
   - **Element Mappings tab**:
     - Configure element type, properties path, and size for different SVG elements
     - Use label prefix mappings for specialized element configurations
     - Customize SVG element behavior based on element labels
4. Process SVG
5. Copy/save results
6. For SCADA export, configure:
   - Project Title, Parent Project, View Name, SVG URL
   - Image and View Dimensions
7. Export SCADA project as zip

## Troubleshooting

### Common Issues
- **Application won't start**: Ensure you have extracted all files including config.json
- **SVG not properly processed**: Check that your SVG file follows standard format
- **Missing elements**: Verify that SVG elements have proper types and attributes
- **Rotation issues**: Check SVG transform attributes format

### Windows Specific Issues
- **Missing dependencies**: Install Visual C++ Redistributable if needed
- **Icon problems**: Check file permissions and antivirus settings

If problems persist, please contact support with error details.

## License
[Standard Automation License]

## Acknowledgments
- Built for automation standard systems
- Uses open-source Python libraries for XML processing and GUI 