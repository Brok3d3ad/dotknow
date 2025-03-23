# SVG Processor - User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Main Interface](#main-interface)
5. [Element Mappings](#element-mappings)
6. [SCADA Project Export](#scada-project-export)
7. [Working with SVG Files](#working-with-svg-files)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [Technical Reference](#technical-reference)

## Introduction

The SVG Processor is a specialized tool designed to convert SVG (Scalable Vector Graphics) files into JSON format for use in automation systems, particularly Ignition SCADA. The application allows for precise control over how SVG elements are processed, named, and positioned.

### Key Capabilities

- Process SVG files containing various element types (rectangles, circles, paths, etc.)
- Apply custom mappings for different SVG element types
- Configure element naming with prefixes and suffixes
- Handle complex SVG transformations (translate, rotate, scale)
- Export results as JSON or complete SCADA project packages

### Intended Audience

This tool is primarily designed for:
- Automation engineers
- SCADA system developers
- HMI designers
- Process visualization specialists

## Installation

### Windows Installation
1. Download the latest release from the distribution folder
2. Extract the ZIP file to your preferred location
3. Run `SVG_Processor.exe` directly - no installation required

### From Source Code
1. Ensure you have Python 3.6 or later installed
2. Clone or download the repository
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python svg_processor_gui.py`

## Getting Started

### Quick Start Guide

1. **Launch the application**: Double-click the executable or run via command line
2. **Select an SVG file**: Click "Browse" to select your SVG file
3. **Configure element mappings**: Set up how different SVG elements should be processed
4. **Process the SVG**: Click "Process SVG" to convert the file
5. **View results**: Review the transformed elements in the Results tab
6. **Export or copy**: Use "Copy to Clipboard" or "Save to File" to export the JSON

### First-Time Setup Checklist

- [ ] Configure default element mappings
- [ ] Set up SCADA project settings
- [ ] Test with a simple SVG file
- [ ] Save configuration for future use

## Main Interface

The application interface is divided into several sections:

### Top Section
- **SVG File Selection**: Browse and select the input SVG file
- **Action Buttons**: Process SVG, Copy, Save, Clear, Export SCADA

### Configuration Tabs
- **SCADA Project**: Configure SCADA project settings
- **Element Mappings**: Define how SVG elements are processed
- **Results**: View processed elements and JSON output
- **Export Log**: View detailed export operations log

### Status Bar
- Shows current application status and operation feedback

## Element Mappings

The Element Mappings tab is where you configure how different SVG elements are processed and named.

### Element Mapping Columns

1. **SVG Element Type**: The type of SVG element (rect, circle, path, etc.)
2. **Label Prefix**: Prefix in the element's label to identify specific elements
3. **Output Element Type**: The type assigned to the element in the output
4. **Properties Path**: Path to properties in the target system
5. **Size (WxH)**: Width and height for the output element
6. **Offset (X,Y)**: Positional adjustments for fine-tuning
7. **Final Prefix**: Prefix added to the final element name
8. **Final Suffix**: Suffix added to the final element name

### Understanding Label Prefixes

Label prefixes in your SVG file help identify and categorize elements. For example:
- `PPI_Conveyor1`: "PPI" is the label prefix
- `CON_Motor2`: "CON" is the label prefix

When the processor finds elements with matching prefixes, it applies the appropriate mappings.

### Final Prefix and Suffix Features

**Final Prefix** and **Final Suffix** are powerful features that let you modify element names during processing:

- **Final Prefix**: Added to the beginning of element names after cleaning
  - Example: Adding "BTN_" makes "Conveyor1" become "BTN_Conveyor1"
  - Underscores (_) are automatically added if not included
  
- **Final Suffix**: Added to the end of element names after cleaning
  - Example: Adding "status" makes "Conveyor1" become "Conveyor1_status"
  - Underscores (_) are automatically added if not included

These features are especially useful for:
- Ensuring consistent naming conventions
- Adding standardized prefixes for element categorization
- Tagging elements with specific identifiers for the target system
- Correcting typos or inconsistencies in original SVG element names

### Working with Element Mappings

#### Adding New Mappings
1. Click "Add New Mapping" button
2. Fill in the required fields
3. The mapping will be saved automatically

#### Removing Mappings
Click the "×" button on the right of any mapping row to remove it.

#### Best Practices for Mappings
- Use consistent label prefixes in your SVG files
- Create specific mappings for commonly used elements
- Use descriptive naming for better maintainability
- Configure size and offsets precisely for your target system

## SCADA Project Export

The application can export processed SVG elements as a complete SCADA project package.

### Export Configuration

1. **Project Title**: Name for the SCADA project
2. **Parent Project**: Parent project in the SCADA system
3. **View Name**: Name of the view in the SCADA system
4. **SVG URL**: URL to the SVG file (for background image)
5. **Image Dimensions**: Width and height of the background image
6. **Default Size**: Default dimensions for the view

### Export Process

1. Configure export settings in the SCADA Project tab
2. Process the SVG file
3. Click "Export SCADA Project"
4. Choose a location to save the ZIP file
5. Import the ZIP into your SCADA system

### Export Structure

The exported ZIP file contains a complete project structure:
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

## Working with SVG Files

### Preparing SVG Files

For best results, follow these guidelines when creating SVG files:

1. **Element Names**: Use consistent naming with prefixes
   - Example: `PPI_Conveyor1`, `PPI_Conveyor2`
   
2. **Element Structure**: Keep elements organized
   - Group related elements
   - Use clear hierarchy
   
3. **File Properties**: Set appropriate dimensions
   - Ensure proper viewBox setting
   - Use consistent measurement units

### SVG Element Types Supported

- **Rectangle** (`rect`): Basic rectangle shapes
- **Circle** (`circle`): Circular elements
- **Ellipse** (`ellipse`): Oval shapes
- **Line** (`line`): Straight lines
- **Polyline** (`polyline`): Connected line segments
- **Polygon** (`polygon`): Closed shapes with multiple sides
- **Path** (`path`): Complex vector paths

### Using Inkscape for SVG Creation

1. Create your drawing in Inkscape
2. Label your elements with appropriate prefixes
   - Right-click > Object Properties > Label
   - Format: `PREFIX_ElementName`
3. Save as Plain SVG

## Advanced Features

### Rotation Handling

The processor supports rotation in several ways:

1. **Transform Rotations**: Automatically extracts rotation from SVG transforms
2. **Suffix Rotations**: Uses element name suffixes to set rotation
   - `_r`: 0 degrees (right)
   - `_d`: 90 degrees (down)
   - `_l`: 180 degrees (left)
   - `_u`: 270 degrees (up)

### Working with Groups

SVG groups (`<g>` elements) are handled specially:

1. **Group Prefixes**: Prefix from a group can be applied to all elements
2. **Group Rotation**: Rotation can cascade to child elements
3. **Element Priority**: Individual element settings override group settings

## Troubleshooting

### Common Issues and Solutions

#### Element Not Appearing in Output

**Possible causes:**
- Element doesn't match any defined mapping
- Element has incompatible transformation
- Element type not supported

**Solutions:**
- Check element label prefixes
- Verify element mapping configuration
- Ensure element is a supported type

#### Incorrect Element Positioning

**Possible causes:**
- SVG transformation issues
- Offset configuration incorrect
- Path coordinate extraction problems

**Solutions:**
- Check SVG transform attributes
- Adjust offset values in element mapping
- For path elements, verify coordinate representation

#### Final Prefix/Suffix Not Applied

**Possible causes:**
- Mapping not correctly set up
- Typo in prefix/suffix field
- Element doesn't match the mapping

**Solutions:**
- Verify the element type and label prefix match your mapping
- Check for spaces or special characters in prefix/suffix fields
- Ensure the correct mapping is being selected for your element

### Debugging Tips

1. **Check Results Tab**: Review the processed JSON for issues
2. **Export Log**: Detailed information about processing steps
3. **Command Line**: Run from command line to see detailed messages

## Best Practices

### Configuration Management

- **Save Configurations**: Save your configurations for reuse
- **Standardize Mappings**: Create standard mappings for common elements
- **Document Conventions**: Document your prefix and naming conventions

### Workflow Optimization

1. **Template Files**: Create template SVG files with proper naming
2. **Batch Processing**: Process multiple files using the same configuration
3. **Validation**: Test with small files before processing large SVGs

### Naming Conventions

- **Label Prefixes**: Keep short but descriptive (3-4 characters)
- **Final Prefixes**: Use for categorization in target system
- **Final Suffixes**: Use for state or type indicators

## Technical Reference

### Configuration File Structure

The application saves settings in a JSON configuration file:

```json
{
  "file_path": "path/to/file.svg",
  "project_title": "My Project",
  "parent_project": "com.example.project",
  "view_name": "MyView",
  "svg_url": "http://example.com/image.svg",
  "image_width": "800",
  "image_height": "600",
  "default_width": "14",
  "default_height": "14",
  "element_mappings": [
    {
      "svg_type": "rect",
      "element_type": "ia.display.view",
      "label_prefix": "PPI",
      "props_path": "Symbol-Views/Equipment-Views/Status",
      "width": 14,
      "height": 14,
      "x_offset": 0,
      "y_offset": 0,
      "final_prefix": "BTN",
      "final_suffix": "status"
    }
  ]
}
```

### Command Line Usage

The application can be run from the command line:

```
python svg_processor_gui.py
```

### Output JSON Format

The processed elements are output in this format:

```json
[
  {
    "type": "ia.display.view",
    "position": {
      "translate": {"x": 100, "y": 200},
      "size": {"width": 14, "height": 14}
    },
    "props": {
      "path": "Symbol-Views/Equipment-Views/Status"
    },
    "meta": {
      "id": "rect1",
      "name": "BTN_Conveyor1_status",
      "originalName": "PPI_Conveyor1",
      "elementPrefix": "PPI",
      "finalPrefixApplied": "BTN_",
      "finalSuffixApplied": "_status"
    }
  }
]
```

---

This manual is for SVG Processor version 1.12.0. For updates and support, please refer to the project documentation. 