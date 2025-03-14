import json
import os
import shutil
import sys

def merge_elements_to_view(view_json_path):
    """Merge elements from element.json into the view JSON file."""
    # Path to the element.json file
    element_json_path = "element.json"
    
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
        # Load the elements
        with open(element_json_path, 'r') as f:
            elements = json.load(f)
        
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

def create_update_script():
    # Paths
    source_path = r"C:\Program Files\Inductive Automation\Ignition\data\projects\MTN6_SCADA\com.inductiveautomation.perspective\views\Detailed-Views\TestView\view.json"
    temp_path = "temp_view.json"
    result_path = "updated_view.json"
    batch_file_path = "update_view.bat"
    
    try:
        # First try to read the existing view file
        if os.path.exists(source_path):
            print(f"Reading original view.json from: {source_path}")
            # Copy the file locally
            try:
                shutil.copy2(source_path, temp_path)
                print(f"Original view.json copied to: {temp_path}")
            except Exception as copy_e:
                print(f"Warning: Could not copy file: {copy_e}")
                print("Creating a new file instead")
                create_default_view(temp_path)
        else:
            print(f"Warning: Source view.json does not exist at {source_path}")
            print("Creating a new view.json file with default structure")
            # Create a new default file
            create_default_view(temp_path)
        
        # Merge the elements by appending to the existing view
        print("Appending SVG elements to the existing view...")
        merge_elements_to_view(temp_path)
        
        # Rename the merged file to finalized result
        if os.path.exists(temp_path):
            shutil.move(temp_path, result_path)
            print(f"Updated view saved to: {result_path}")
        else:
            print(f"Error: Expected {temp_path} to exist but it doesn't.")
            sys.exit(1)
        
        # Create the batch file
        create_batch_file(result_path, source_path, batch_file_path)
        
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
                                    "expression": ""
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

if __name__ == "__main__":
    create_update_script() 