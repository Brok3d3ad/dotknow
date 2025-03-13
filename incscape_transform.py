import xml.etree.ElementTree as ET
import json
import re
import math
import numpy as np
import os
import sys
import shutil
import argparse
from xml.dom import minidom

def parse_transform(transform_str):
    """Parse SVG transform attribute and return transformation matrix."""
    if not transform_str:
        return np.identity(3)
    
    # Initialize transformation matrix as identity
    matrix = np.identity(3)
    
    # Find all transformation operations
    for op in re.finditer(r'(\w+)\s*\(([^)]*)\)', transform_str):
        op_name = op.group(1)
        params = [float(x) for x in re.findall(r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', op.group(2))]
        
        if op_name == 'matrix':
            # matrix(a,b,c,d,e,f) -> [a c e; b d f; 0 0 1]
            if len(params) == 6:
                transform_matrix = np.array([
                    [params[0], params[2], params[4]],
                    [params[1], params[3], params[5]],
                    [0, 0, 1]
                ])
                matrix = np.matmul(matrix, transform_matrix)
        
        elif op_name == 'translate':
            # translate(tx, ty) -> [1 0 tx; 0 1 ty; 0 0 1]
            tx = params[0]
            ty = params[1] if len(params) > 1 else 0
            translation_matrix = np.array([
                [1, 0, tx],
                [0, 1, ty],
                [0, 0, 1]
            ])
            matrix = np.matmul(matrix, translation_matrix)
        
        elif op_name == 'scale':
            # scale(sx, sy) -> [sx 0 0; 0 sy 0; 0 0 1]
            sx = params[0]
            sy = params[1] if len(params) > 1 else sx
            scale_matrix = np.array([
                [sx, 0, 0],
                [0, sy, 0],
                [0, 0, 1]
            ])
            matrix = np.matmul(matrix, scale_matrix)
        
        elif op_name == 'rotate':
            # rotate(angle, cx, cy) -> rotation matrix
            angle_rad = math.radians(params[0])
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            if len(params) == 3:  # rotate around point
                cx, cy = params[1], params[2]
                # Translate to origin, rotate, translate back
                translation_to_origin = np.array([
                    [1, 0, -cx],
                    [0, 1, -cy],
                    [0, 0, 1]
                ])
                rotation = np.array([
                    [cos_a, -sin_a, 0],
                    [sin_a, cos_a, 0],
                    [0, 0, 1]
                ])
                translation_back = np.array([
                    [1, 0, cx],
                    [0, 1, cy],
                    [0, 0, 1]
                ])
                transform = np.matmul(np.matmul(translation_to_origin, rotation), translation_back)
                matrix = np.matmul(matrix, transform)
            else:  # rotate around origin
                rotation = np.array([
                    [cos_a, -sin_a, 0],
                    [sin_a, cos_a, 0],
                    [0, 0, 1]
                ])
                matrix = np.matmul(matrix, rotation)
    
    return matrix

def apply_transform(point, transform_matrix):
    """Apply transformation matrix to a point."""
    # Convert point to homogeneous coordinates
    point_h = np.array([point[0], point[1], 1])
    
    # Apply transformation
    transformed = np.matmul(transform_matrix, point_h)
    
    # Convert back from homogeneous coordinates
    return transformed[0], transformed[1]

def get_all_transforms(element, doc):
    """Get all transforms from element up through parent groups."""
    transform_matrices = []
    
    # Get transform from the current element
    transform_str = element.getAttribute('transform')
    if transform_str:
        transform_matrices.append(parse_transform(transform_str))
    
    # Get transforms from parent groups
    current = element.parentNode
    while current and current.nodeType == current.ELEMENT_NODE:
        if current.tagName == 'g':
            transform_str = current.getAttribute('transform')
            if transform_str:
                transform_matrices.append(parse_transform(transform_str))
        current = current.parentNode
    
    # Combine all transforms (from innermost to outermost)
    combined_matrix = np.identity(3)
    for matrix in reversed(transform_matrices):
        combined_matrix = np.matmul(matrix, combined_matrix)
    
    return combined_matrix

def process_svg(svg_path):
    """Process SVG file and extract rect elements with calculated centers."""
    # Parse the SVG file using minidom for better element hierarchy handling
    doc = minidom.parse(svg_path)
    
    # Get SVG dimensions
    svg_element = doc.getElementsByTagName('svg')[0]
    width = float(svg_element.getAttribute('width') or 0)
    height = float(svg_element.getAttribute('height') or 0)
    
    # Find all rect elements
    results = []
    rect_count = 0
    rect_elements = doc.getElementsByTagName('rect')
    
    for rect in rect_elements:
        try:
            rect_count += 1
            # Extract rect attributes
            x = float(rect.getAttribute('x') or 0)
            y = float(rect.getAttribute('y') or 0)
            w = float(rect.getAttribute('width') or 0)
            h = float(rect.getAttribute('height') or 0)
            
            # Calculate center
            center_x = x + w/2
            center_y = y + h/2
            
            # Get all transforms (including parent group transforms)
            transform_matrix = get_all_transforms(rect, doc)
            
            # Apply transform
            center_x, center_y = apply_transform((center_x, center_y), transform_matrix)
            
            # Apply the requested offset (-8 pixels in both x and y directions)
            offset_center_x = center_x - 7
            offset_center_y = center_y - 7
            
            # Get the original rectangle name or ID
            rect_id = rect.getAttribute('id') or ""
            rect_name = rect.getAttribute('inkscape:label') or ""
            
            # Use the ID or label as name, or fallback to a generated name
            element_name = rect_id or rect_name or f"Rect_{rect_count}"
            
            # Log the original, transformed, and offset coordinates
            print(f"Rect #{rect_count}: Original name/id: {element_name}, Original center ({x + w/2}, {y + h/2}), Transformed ({center_x}, {center_y}), With offset ({offset_center_x}, {offset_center_y})")
            
            # Create element JSON object
            element = {
                "type": "ia.display.view",
                "version": 0,
                "props": {
                    "path": "Symbol-Views/Equipment-Views/Status",
                    "params": {
                        "directionLeft": False,
                        "forceFaultStatus": None,
                        "forceRunningStatus": None,
                        "tagProps": [
                            "DF410/BL02_383",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value"
                        ]
                    }
                },
                "meta": {
                    "name": element_name,
                    "originalName": rect_id or rect_name or "",
                    "rectNumber": rect_count
                },
                "position": {
                    "x": offset_center_x,
                    "y": offset_center_y,
                    "height": 14,  # Fixed height in pixels
                    "width": 14    # Fixed width in pixels
                },
                "custom": {}
            }
            
            results.append(element)
        except (ValueError, TypeError) as e:
            print(f"Error processing rect #{rect_count}: {e}")
    
    print(f"Processed {rect_count} rectangles, successfully converted {len(results)}")
    return results

def merge_elements_to_view(view_json_path, elements):
    """Merge elements from element.json into the view JSON file."""
    # Create a backup of the view.json file if it exists
    backup_path = None
    if os.path.exists(view_json_path):
        backup_path = view_json_path + ".backup"
        try:
            shutil.copy2(view_json_path, backup_path)
            print(f"Created backup of view.json at {backup_path}")
        except Exception as e:
            print(f"Warning: Unable to create backup: {e}")
    
    try:
        # Load the view configuration
        with open(view_json_path, 'r') as f:
            view_config = json.load(f)
            print(f"Successfully read existing view configuration with {len(view_config.get('root', {}).get('children', []))} elements")
        
        # Access the children array in the view config
        children = view_config.get('root', {}).get('children', [])
        
        # Dictionary to track names we've seen for avoiding duplicates
        existing_names = {child.get('meta', {}).get('name', ''): True for child in children}
        
        # Keep all existing children
        updated_children = children.copy()
        print(f"Preserved all {len(children)} existing elements in the view")
        
        # Add all the elements from element.json
        elements_added = 0
        elements_skipped = 0
        for element in elements:
            # Get the element name
            element_name = element.get('meta', {}).get('name', '')
            
            # Skip if we've already added this element by name
            if element_name in existing_names and element_name:
                print(f"Skipping duplicate element: {element_name}")
                elements_skipped += 1
                continue
            
            # Format the element correctly for view.json
            view_element = {
                "meta": {
                    "name": element_name
                },
                "position": {
                    "height": element.get("position", {}).get("height", 16),
                    "width": element.get("position", {}).get("width", 16),
                    "x": element.get("position", {}).get("x", 0),
                    "y": element.get("position", {}).get("y", 0)
                },
                "props": {
                    "path": "Symbol-Views/Equipment-Views/Status",
                    "params": {
                        "directionLeft": False,
                        "forceFaultStatus": None,
                        "forceRunningStatus": None,
                        "tagProps": [
                            "DF410/BL02_383",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value",
                            "value"
                        ]
                    }
                },
                "type": element.get("type", "ia.display.view")
            }
            
            # Add the new element
            updated_children.append(view_element)
            existing_names[element_name] = True
            print(f"Added element: {element_name}")
            elements_added += 1
        
        # Replace the children in the view config
        view_config['root']['children'] = updated_children
        
        # Write the updated view config back to the file
        with open(view_json_path, 'w') as f:
            json.dump(view_config, f, indent=2)
        
        print(f"Successfully updated view.json with {elements_added} new elements appended ({elements_skipped} skipped)")
        
    except Exception as e:
        print(f"Error updating view.json: {e}")
        # If backup exists, restore it
        if backup_path and os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, view_json_path)
                print(f"Restored backup due to error")
            except Exception as restore_e:
                print(f"Error restoring backup: {restore_e}")
        raise e  # Re-raise the exception

def create_default_view(file_path):
    """Create a default view.json file with the correct structure."""
    default_view = {
        "custom": {},
        "params": {},
        "props": {
            "defaultSize": {
                "height": 1028,
                "width": 1850
            }
        },
        "root": {
            "children": [
                {
                    "meta": {
                        "name": "Image"
                    },
                    "position": {
                        "height": 1028,
                        "width": 1850
                    },
                    "propConfig": {
                        "props.source": {
                            "binding": {
                                "config": {
                                    "expression": "\"http://127.0.0.1:5500/Bulk%20Inbund%20Problem%20Solve.svg?var\""
                                },
                                "type": "expr"
                            }
                        }
                    },
                    "props": {
                        "fit": {
                            "mode": "fill"
                        }
                    },
                    "type": "ia.display.image"
                }
            ],
            "meta": {
                "name": "root"
            },
            "type": "ia.container.coord"
        }
    }
    
    with open(file_path, 'w') as f:
        json.dump(default_view, f, indent=2)
    
    print(f"Created default view.json with proper structure at {file_path}")

def create_batch_file(source, destination, batch_path):
    """Create a batch file that will copy the updated view to the Ignition directory."""
    
    # Get absolute paths
    abs_source = os.path.abspath(source)
    
    # Create batch file content
    batch_content = f"""@echo off
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
copy /Y "{abs_source}" "{destination}"

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
"""

    # Write the batch file
    with open(batch_path, 'w') as f:
        f.write(batch_content)
    
    print(f"Batch file created: {batch_path} (will update the Ignition view)")

def create_update_script(svg_path, view_path=None):
    """Main function that processes SVG and updates the view"""
    
    # Default ignition view path if not provided
    if not view_path:
        view_path = r"C:\Program Files\Inductive Automation\Ignition\data\projects\MTN6_SCADA\com.inductiveautomation.perspective\views\Detailed-Views\TestView\view.json"
    
    temp_path = "temp_view.json"
    result_path = "updated_view.json"
    batch_file_path = "update_view.bat"
    
    try:
        print(f"Processing SVG file: {svg_path}")
        # Process the SVG to get elements
        elements = process_svg(svg_path)
        
        # First try to read the existing view file
        if os.path.exists(view_path):
            print(f"Reading original view.json from: {view_path}")
            # Copy the file locally
            try:
                shutil.copy2(view_path, temp_path)
                print(f"Original view.json copied to: {temp_path}")
            except Exception as copy_e:
                print(f"Warning: Could not copy file: {copy_e}")
                print("Creating a new file instead")
                create_default_view(temp_path)
        else:
            print(f"Warning: Source view.json does not exist at {view_path}")
            print("Creating a new view.json file with default structure")
            # Create a new default file
            create_default_view(temp_path)
        
        # Merge the elements by appending to the existing view
        print("Appending SVG elements to the existing view...")
        merge_elements_to_view(temp_path, elements)
        
        # Rename the merged file to finalized result
        if os.path.exists(temp_path):
            shutil.move(temp_path, result_path)
            print(f"Updated view saved to: {result_path}")
        else:
            print(f"Error: Expected {temp_path} to exist but it doesn't.")
            sys.exit(1)
        
        # Create the batch file
        create_batch_file(result_path, view_path, batch_file_path)
        
        print("\n=== BATCH FILE CREATED ===")
        print(f"A batch file has been created at: {os.path.abspath(batch_file_path)}")
        print("To update the Ignition view:")
        print("1. Right-click on the batch file")
        print("2. Select 'Run as administrator'")
        print("This will update the view in the Ignition installation directory while preserving all existing elements.")
        
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        sys.exit(1)

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Process SVG file and update Ignition view with extracted elements'
    )
    
    # Add command line arguments
    parser.add_argument('-s', '--svg', required=True, help='Path to the SVG file to process')
    parser.add_argument('-v', '--view', help='Path to the Ignition view.json file to update (optional, will use default if not provided)')
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the main function with the provided paths
    create_update_script(args.svg, args.view)

if __name__ == "__main__":
    main() 