import xml.etree.ElementTree as ET
import json
import re
import math
import numpy as np
import os
import argparse
from xml.dom import minidom

class SVGTransformer:
    """Class to handle SVG parsing and transformation of rectangle elements."""
    
    def __init__(self, svg_path, custom_options=None):
        """Initialize with the path to the SVG file and optional custom options."""
        self.svg_path = svg_path
        self.doc = minidom.parse(svg_path)
        self.svg_element = self.doc.getElementsByTagName('svg')[0]
        self.custom_options = custom_options or {}
        
    def get_svg_dimensions(self):
        """Get the dimensions of the SVG document."""
        width = float(self.svg_element.getAttribute('width') or 0)
        height = float(self.svg_element.getAttribute('height') or 0)
        return width, height
    
    def parse_transform(self, transform_str):
        """Parse SVG transform attribute and return transformation matrix."""
        if not transform_str:
            return np.identity(3)
        
        # Initialize transformation matrix as identity
        matrix = np.identity(3)
        
        # Find all transformation operations
        for op in re.finditer(r'(\w+)\s*\(([^)]*)\)', transform_str):
            op_name = op.group(1)
            params = [float(x) for x in re.findall(r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', op.group(2))]
            
            matrix = self._apply_operation_to_matrix(matrix, op_name, params)
        
        return matrix
    
    def _apply_operation_to_matrix(self, matrix, op_name, params):
        """Apply a specific transform operation to the matrix."""
        if op_name == 'matrix' and len(params) == 6:
            transform_matrix = np.array([
                [params[0], params[2], params[4]],
                [params[1], params[3], params[5]],
                [0, 0, 1]
            ])
            return np.matmul(matrix, transform_matrix)
            
        elif op_name == 'translate':
            tx = params[0]
            ty = params[1] if len(params) > 1 else 0
            translation_matrix = np.array([
                [1, 0, tx],
                [0, 1, ty],
                [0, 0, 1]
            ])
            return np.matmul(matrix, translation_matrix)
            
        elif op_name == 'scale':
            sx = params[0]
            sy = params[1] if len(params) > 1 else sx
            scale_matrix = np.array([
                [sx, 0, 0],
                [0, sy, 0],
                [0, 0, 1]
            ])
            return np.matmul(matrix, scale_matrix)
            
        elif op_name == 'rotate':
            return self._handle_rotation(matrix, params)
            
        return matrix  # Return unchanged matrix for unsupported operations
    
    def _handle_rotation(self, matrix, params):
        """Handle rotation transform operations."""
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
            return np.matmul(matrix, transform)
        else:  # rotate around origin
            rotation = np.array([
                [cos_a, -sin_a, 0],
                [sin_a, cos_a, 0],
                [0, 0, 1]
            ])
            return np.matmul(matrix, rotation)
    
    def apply_transform(self, point, transform_matrix):
        """Apply transformation matrix to a point."""
        # Convert point to homogeneous coordinates
        point_h = np.array([point[0], point[1], 1])
        
        # Apply transformation
        transformed = np.matmul(transform_matrix, point_h)
        
        # Convert back from homogeneous coordinates
        return transformed[0], transformed[1]
    
    def get_all_transforms(self, element):
        """Get all transforms from element up through parent groups."""
        transform_matrices = []
        
        # Get transform from the current element
        transform_str = element.getAttribute('transform')
        if transform_str:
            transform_matrices.append(self.parse_transform(transform_str))
        
        # Get transforms from parent groups
        current = element.parentNode
        while current and current.nodeType == current.ELEMENT_NODE:
            if current.tagName == 'g':
                transform_str = current.getAttribute('transform')
                if transform_str:
                    transform_matrices.append(self.parse_transform(transform_str))
            current = current.parentNode
        
        # Combine all transforms (from innermost to outermost)
        combined_matrix = np.identity(3)
        for matrix in reversed(transform_matrices):
            combined_matrix = np.matmul(matrix, combined_matrix)
        
        return combined_matrix
    
    def process_rectangle(self, rect, rect_count):
        """Process a single rectangle element and return its JSON representation."""
        try:
            # Extract rect attributes
            x = float(rect.getAttribute('x') or 0)
            y = float(rect.getAttribute('y') or 0)
            width = float(rect.getAttribute('width') or 0)
            height = float(rect.getAttribute('height') or 0)
            
            # Calculate center
            center_x = x + width/2
            center_y = y + height/2
            
            # Get all transforms (including parent group transforms)
            transform_matrix = self.get_all_transforms(rect)
            
            # Apply transform
            center_x, center_y = self.apply_transform((center_x, center_y), transform_matrix)
            
            # Apply the requested offset (-7 pixels in both x and y directions)
            offset_x = center_x - 7
            offset_y = center_y - 7
            
            # Get element identifiers
            rect_id = rect.getAttribute('id') or ""
            rect_label = rect.getAttribute('inkscape:label') or ""
            
            # Use the inkscape:label as name, or fallback to a numbered format
            element_name = rect_label or f"rect{rect_count}"
            
            # Log processing information
            print(f"Rect #{rect_count}: Original name/id: {element_name}, "
                  f"Original center ({x + width/2}, {y + height/2}), "
                  f"Transformed ({center_x}, {center_y}), "
                  f"With offset ({offset_x}, {offset_y})")
            
            # Create and return element JSON object
            return self.create_element_json(element_name, rect_id, rect_label, rect_count, offset_x, offset_y)
            
        except (ValueError, TypeError) as e:
            print(f"Error processing rect #{rect_count}: {e}")
            return None
    
    def create_element_json(self, element_name, rect_id, rect_label, rect_number, x, y):
        """Create a JSON object for a rectangle element."""
        # Get custom values from options or use defaults
        element_type = self.custom_options.get('type', "ia.display.view")
        props_path = self.custom_options.get('props_path', "Symbol-Views/Equipment-Views/Status")
        element_height = self.custom_options.get('height', 14)
        element_width = self.custom_options.get('width', 14)
        
        return {
            "type": element_type,
            "version": 0,
            "props": {
                "path": props_path,
                "params": {
                    "directionLeft": False,
                    "forceFaultStatus": None,
                    "forceRunningStatus": None,
                    "tagProps": [
                        element_name,
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
                "originalName": rect_id or rect_label or "",
                "rectNumber": rect_number
            },
            "position": {
                "x": x,
                "y": y,
                "height": element_height,  # Height from custom options or default
                "width": element_width     # Width from custom options or default
            },
            "custom": {}
        }
    
    def process_svg(self):
        """Process SVG file and extract rect elements with calculated centers."""
        # Find all rect elements
        results = []
        rect_count = 0
        rect_elements = self.doc.getElementsByTagName('rect')
        
        for rect in rect_elements:
            rect_count += 1
            element_json = self.process_rectangle(rect, rect_count)
            if element_json:
                results.append(element_json)
        
        print(f"Processed {rect_count} rectangles, successfully converted {len(results)}")
        return results

def save_json_to_file(data, output_file):
    """Save data to a JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Elements saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving elements to file: {e}")
        return False

def validate_with_existing(new_elements, existing_file='elements.json'):
    """Compare newly generated elements with existing ones to validate."""
    try:
        if not os.path.exists(existing_file):
            print(f"No existing file {existing_file} to validate against.")
            return
            
        with open(existing_file, 'r') as f:
            existing_elements = json.load(f)
            
        if len(new_elements) != len(existing_elements):
            print(f"Warning: Element count mismatch. New: {len(new_elements)}, Existing: {len(existing_elements)}")
        
        # Compare all elements
        mismatches = 0
        compare_length = min(len(new_elements), len(existing_elements))
        
        for idx in range(compare_length):
            new_el = new_elements[idx]
            old_el = existing_elements[idx]
            
            # Check position values (most critical)
            pos_x_diff = abs(new_el["position"]["x"] - old_el["position"]["x"])
            pos_y_diff = abs(new_el["position"]["y"] - old_el["position"]["y"])
            pos_match = pos_x_diff < 0.001 and pos_y_diff < 0.001
            
            # Check name and metadata
            name_match = new_el["meta"]["name"] == old_el["meta"]["name"]
            rect_num_match = new_el["meta"]["rectNumber"] == old_el["meta"]["rectNumber"]
            tag_props_match = new_el["props"]["params"]["tagProps"] == old_el["props"]["params"]["tagProps"]
            
            if not (pos_match and name_match and rect_num_match and tag_props_match):
                mismatches += 1
                if mismatches <= 5:  # Limit reporting to first 5 mismatches to avoid flooding console
                    print(f"Mismatch at element {idx}:")
                    if not pos_match:
                        print(f"  Position: New ({new_el['position']['x']}, {new_el['position']['y']}) vs "
                              f"Old ({old_el['position']['x']}, {old_el['position']['y']})")
                    if not name_match:
                        print(f"  Name: New '{new_el['meta']['name']}' vs Old '{old_el['meta']['name']}'")
                    if not rect_num_match:
                        print(f"  Rectangle Number: New {new_el['meta']['rectNumber']} vs Old {old_el['meta']['rectNumber']}")
                    if not tag_props_match:
                        print(f"  Tag Properties mismatch")
        
        if mismatches == 0:
            print("Validation successful! All elements match.")
        else:
            print(f"Validation found {mismatches} mismatches out of {compare_length} elements.")
            
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Entry point for the script."""
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Process SVG file and extract elements as JSON objects'
    )
    
    # Add command line arguments
    parser.add_argument('-s', '--svg', required=True, help='Path to the SVG file to process')
    parser.add_argument('-o', '--output', default='elements.json', help='Output JSON file path (default: elements.json)')
    parser.add_argument('--print-only', action='store_true', help='Only print the JSON objects without saving to file')
    parser.add_argument('--validate', action='store_true', help='Validate output against existing elements.json')
    
    # Parse the arguments
    args = parser.parse_args()
    
    try:
        print(f"Processing SVG file: {args.svg}")
        
        # Create transformer and process SVG
        transformer = SVGTransformer(args.svg)
        elements = transformer.process_svg()
        
        # Save or print elements based on command line argument
        if args.print_only:
            print("\nExtracted JSON objects:\n")
            print(json.dumps(elements, indent=2))
        else:
            save_json_to_file(elements, args.output)
        
        # Validate if requested
        if args.validate:
            validate_with_existing(elements)
        
        print(f"\nSuccessfully processed {len(elements)} elements from the SVG file.")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    main() 