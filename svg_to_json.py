import xml.etree.ElementTree as ET
import json
import re
import math
import numpy as np
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

def main():
    svg_path = "Bulk Inbund Problem Solve.svg"
    output_path = "element.json"
    
    # Process the SVG
    elements = process_svg(svg_path)
    
    # Write the results to JSON
    with open(output_path, 'w') as f:
        json.dump(elements, f, indent=2)
    
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main() 