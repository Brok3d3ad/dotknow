import xml.etree.ElementTree as ET
import json
import re
import math
import numpy as np
import os
import argparse
from xml.dom import minidom

class SVGTransformer:
    """Class to handle SVG parsing and transformation of SVG elements."""
    
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
        
        try:
            # Find all transformation operations
            for op in re.finditer(r'(\w+)\s*\(([^)]*)\)', transform_str):
                op_name = op.group(1)
                params_str = op.group(2)
                
                # Extract parameters safely
                try:
                    params = [float(x) for x in re.findall(r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', params_str)]
                    matrix = self._apply_operation_to_matrix(matrix, op_name, params)
                except (ValueError, TypeError) as e:
                    print(f"Error parsing transform parameters '{params_str}': {e}")
                    # Continue with the current matrix rather than failing
        except Exception as e:
            print(f"Error parsing transform '{transform_str}': {e}")
            return np.identity(3)
            
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
        
        # For debugging
        print(f"Applying transform to point {point} with matrix {transform_matrix} → result: ({transformed[0]}, {transformed[1]})")
        
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
    
    def get_element_type_for_svg_type(self, svg_type):
        """
        Determine the element type to use based on SVG element type.
        Uses the element_type_mapping from custom_options if available,
        otherwise falls back to the default element type.
        """
        # Get the element type mapping from custom options, or use empty dict
        element_type_mapping = self.custom_options.get('element_type_mapping', {})
        
        # If we have a mapping for this SVG element type, use it
        if svg_type in element_type_mapping and element_type_mapping[svg_type]:
            return element_type_mapping[svg_type]
        
        # Fall back to the general element type
        return self.custom_options.get('type', "ia.display.view")
    
    def get_element_type_for_svg_type_and_label(self, svg_type, label_prefix):
        """Get the appropriate element type for an SVG type and label."""
        # Find the right mapping to use - first exact match, then fallback
        exact_match = None
        fallback_match = None
        
        print(f"Looking for mapping for svg_type={svg_type}, label_prefix='{label_prefix}'")
        
        # First pass: look for an exact match
        if label_prefix:  # Only look for exact match if we have a prefix
            for mapping in self.custom_options['element_mappings']:
                if mapping['svg_type'] == svg_type and mapping.get('label_prefix', '') == label_prefix:
                    exact_match = mapping
                    print(f"Found exact match: {mapping}")
                    break
        
        # Second pass: look for a fallback match (no prefix)
        for mapping in self.custom_options['element_mappings']:
            if mapping['svg_type'] == svg_type and not mapping.get('label_prefix', ''):
                fallback_match = mapping
                print(f"Found fallback match: {mapping}")
                break
        
        # Use the exact match if found, otherwise try the fallback
        if exact_match and 'element_type' in exact_match:
            return exact_match['element_type']
        elif fallback_match and 'element_type' in fallback_match:
            return fallback_match['element_type']
        
        # Default fallback
        return self.custom_options.get('type', "ia.display.view")

    def create_element_json(self, element_name, element_id, element_label, element_count, x, y, svg_type, label_prefix, rotation_angle=0, element_width=None, element_height=None, x_offset=0, y_offset=0, original_name=None, debug_buffer=None, has_prefix_mapping=None):
        """Create a JSON object for an SVG element."""
        # Output debugging information
        if original_name is None:
            original_name = element_id or element_label or ""
            
        # Now that the element is fully processed, print the debug header
        print(f"\n==== DEBUG FOR ELEMENT {element_count}: {element_name} (Original: {original_name}) ====")
        print(f"SVG Type: {svg_type}, Position: ({x}, {y}), Rotation: {rotation_angle}deg")
        print(f"Using element size: {element_width}x{element_height}")
        print(f"Mapping information: Prefix: {label_prefix}, Has mapping: {has_prefix_mapping}")
        print(f"Applied offsets: x_offset={x_offset}, y_offset={y_offset}")
        
        # Print all the buffered debug messages if provided
        if debug_buffer:
            for msg in debug_buffer:
                print(f"  {msg}")
                
        print("==== END DEBUG ====")
        
        # Find the right mapping to use
        exact_match = None
        fallback_match = None
        
        # First look for an exact match with label prefix
        if label_prefix:
            for mapping in self.custom_options.get('element_mappings', []):
                if mapping['svg_type'] == svg_type and mapping.get('label_prefix', '') == label_prefix:
                    exact_match = mapping
                    print(f"Found exact match: {mapping}")
                    break
        
        # Then look for a fallback with no prefix
        for mapping in self.custom_options.get('element_mappings', []):
            if mapping['svg_type'] == svg_type and not mapping.get('label_prefix', ''):
                fallback_match = mapping
                if not exact_match:  # Only print if we haven't found an exact match
                    print(f"Found fallback match: {mapping}")
                break
        
        # Use the appropriate mapping
        mapping_to_use = exact_match or fallback_match
        
        # Get element type and props path from mapping
        element_type = "ia.display.view"  # Default
        props_path = "Symbol-Views/Equipment-Views/Status"  # Default
        
        if mapping_to_use:
            element_type = mapping_to_use.get('element_type', element_type)
            props_path = mapping_to_use.get('props_path', props_path)
        
        # Preserve rotation angle as float for accuracy, just format it for output
        try:
            rotation_angle = float(rotation_angle)
        except (ValueError, TypeError):
            rotation_angle = 0
            
        print(f"Final rotation to use: {rotation_angle}deg")
        
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
                "originalName": original_name,
                "elementNumber": element_count,
                "svgType": svg_type,
                "labelPrefix": label_prefix,
                "offsets": {
                    "x": x_offset,
                    "y": y_offset
                }
            },
            "position": {
                "x": x,
                "y": y,
                "height": element_height,
                "width": element_width,
                "rotate": {
                    "anchor": "50% 50%",
                    "angle": f"{rotation_angle}deg"
                }
            },
            "custom": {}
        }
    
    def clean_element_name(self, element_name, prefix=None, suffix=None, has_prefix_mapping=False):
        """Clean element name by removing prefix and suffix if configured.
        Also removes adjacent underscores.
        
        Args:
            element_name (str): Original element name
            prefix (str): Identified prefix to remove (if any)
            suffix (str): Identified suffix to remove (if any)
            has_prefix_mapping (bool): Whether a mapping exists for the prefix
            
        Returns:
            str: Cleaned element name
        """
        cleaned_name = element_name
        
        # Remove prefix ONLY if we have a mapping for it
        if prefix and has_prefix_mapping and cleaned_name.startswith(prefix):
            # Remove prefix
            cleaned_name = cleaned_name[len(prefix):]
            # Remove underscore after prefix if present
            if cleaned_name.startswith('_'):
                cleaned_name = cleaned_name[1:]
        
        # Remove suffix if it exists and is configured - this works independently of prefix
        if suffix and len(cleaned_name) > 0:
            # When removing just the suffix, remove it only from the very end
            if cleaned_name.endswith(suffix):
                # Remove suffix
                cleaned_name = cleaned_name[:-len(suffix)]
                # Remove underscore before suffix if present
                if cleaned_name.endswith('_'):
                    cleaned_name = cleaned_name[:-1]
        
        # If the name is empty after cleaning, revert to original
        if not cleaned_name:
            return element_name
            
        return cleaned_name
    
    def process_element(self, element, element_count, svg_type):
        """Process a single SVG element and return its JSON representation."""
        try:
            # Debug buffer to collect all debug messages for this element
            debug_buffer = []
            
            # Extract element attributes and calculate center based on element type
            if svg_type == 'rect':
                x = float(element.getAttribute('x') or 0)
                y = float(element.getAttribute('y') or 0)
                width = float(element.getAttribute('width') or 0)
                height = float(element.getAttribute('height') or 0)
                # Calculate center of the original rect
                orig_center_x = x + width/2
                orig_center_y = y + height/2
                # Keep track of original dimensions
                original_width = width
                original_height = height
            elif svg_type == 'circle':
                cx = float(element.getAttribute('cx') or 0)
                cy = float(element.getAttribute('cy') or 0)
                r = float(element.getAttribute('r') or 0)
                # The center is already given for circles
                orig_center_x, orig_center_y = cx, cy
                original_width = r * 2
                original_height = r * 2
            elif svg_type == 'ellipse':
                cx = float(element.getAttribute('cx') or 0)
                cy = float(element.getAttribute('cy') or 0)
                rx = float(element.getAttribute('rx') or 0)
                ry = float(element.getAttribute('ry') or 0)
                # The center is already given for ellipses
                orig_center_x, orig_center_y = cx, cy
                original_width = rx * 2
                original_height = ry * 2
            elif svg_type == 'line':
                x1 = float(element.getAttribute('x1') or 0)
                y1 = float(element.getAttribute('y1') or 0)
                x2 = float(element.getAttribute('x2') or 0)
                y2 = float(element.getAttribute('y2') or 0)
                # Calculate midpoint of the line
                orig_center_x = (x1 + x2) / 2
                orig_center_y = (y1 + y2) / 2
                original_width = abs(x2 - x1)
                original_height = abs(y2 - y1)
            elif svg_type in ['polyline', 'polygon', 'path']:
                # For these complex types, we'll use a simple approach
                # In a real implementation, you'd calculate the bounding box
                orig_center_x, orig_center_y = 0, 0
                original_width = 10  # Default
                original_height = 10  # Default
                
                # Special handling for path elements - extract starting coordinates from d attribute
                if svg_type == 'path':
                    d_attr = element.getAttribute('d')
                    if d_attr:
                        debug_buffer.append(f"Processing path with data: {d_attr}")
                        
                        # For special debugging
                        debug_buffer.append(f"*** Y-COORDINATE DEBUG ***")
                        
                        # Extract the first x,y coordinates from the path data
                        # Path data typically starts with "m" or "M" followed by x,y coordinates
                        # Try to match coordinates with comma separator (most common)
                        comma_separated = re.findall(r'[mM]\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*,\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)', d_attr)
                        
                        # If not found, try to match coordinates with space separator
                        space_separated = []
                        if not comma_separated:
                            space_match = re.search(r'[mM]\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)', d_attr)
                            if space_match:
                                space_separated = [(space_match.group(1), space_match.group(2))]
                        
                        # Use comma_separated if found, otherwise use space_separated
                        path_coords = comma_separated or space_separated
                        
                        # For debugging
                        if comma_separated:
                            debug_buffer.append(f"Found comma-separated coordinates")
                        elif space_separated:
                            debug_buffer.append(f"Found space-separated coordinates")
                        else:
                            debug_buffer.append(f"Could not find coordinates with standard patterns")
                        
                        # Determine if we're using relative coordinates (lowercase 'm' means relative)
                        is_relative = d_attr.strip().startswith('m')
                        
                        if path_coords:
                            try:
                                # Extract the raw coordinate values from the path data
                                x_str = path_coords[0][0]
                                y_str = path_coords[0][1]
                                
                                debug_buffer.append(f"Raw extracted values - x_str: '{x_str}', y_str: '{y_str}'")
                                
                                # Convert to float
                                orig_center_x = float(x_str)
                                orig_center_y = float(y_str)
                                
                                debug_buffer.append(f"After float conversion - x: {orig_center_x}, y: {orig_center_y}")
                                debug_buffer.append(f"Extracted path starting coordinates: ({orig_center_x}, {orig_center_y}) - {'Relative' if is_relative else 'Absolute'} coordinates")
                            except (ValueError, IndexError) as e:
                                debug_buffer.append(f"Error extracting path coordinates: {e}")
                        else:
                            debug_buffer.append(f"Could not extract coordinates from path data: {d_attr}")
                
                debug_buffer.append(f"Warning: {svg_type} element support is basic - center may not be accurate")
            else:
                # Default case for unsupported types
                orig_center_x, orig_center_y = 0, 0
                original_width = 10  # Default
                original_height = 10  # Default
                debug_buffer.append(f"Warning: Unsupported element type {svg_type}")
            
            # Get transformation matrix from all parent transforms
            transform_matrix = self.get_all_transforms(element)
            
            # Print the original transform string for debugging
            transform_str = element.getAttribute('transform')
            if transform_str:
                debug_buffer.append(f"Element has transform: {transform_str}")
            
            # Extract rotation angle from the transform
            rotation_angle = self.extract_rotation_from_transform(element)
            
            # Apply transform to the center point to get transformed center
            transformed_center_x, transformed_center_y = self.apply_transform(
                (orig_center_x, orig_center_y), transform_matrix
            )
            
            # For debugging - print transformation details for path elements
            if svg_type == 'path':
                debug_buffer.append(f"TRANSFORM DEBUG - Original: ({orig_center_x}, {orig_center_y}), Transformed: ({transformed_center_x}, {transformed_center_y})")
                
                # Print transform matrix if available
                if transform_matrix is not None and not np.array_equal(transform_matrix, np.identity(3)):
                    debug_buffer.append(f"Transform Matrix: {transform_matrix}")
            
            # Get element identifiers
            element_id = element.getAttribute('id') or ""
            element_label = element.getAttribute('inkscape:label') or ""
            element_name = element_label or f"{svg_type}{element_count}"
            original_name = element_name  # Store original name
            
            # Get the first 3 letters of the label if it exists
            label_prefix = ""
            if element_label and len(element_label) >= 3:
                label_prefix = element_label[:3]
            
            # Check if we have a mapping for this prefix
            has_prefix_mapping = False
            exact_prefix_match = None
            
            if 'element_mappings' in self.custom_options and label_prefix:
                for mapping in self.custom_options['element_mappings']:
                    if mapping.get('label_prefix', '') == label_prefix:
                        has_prefix_mapping = True
                        exact_prefix_match = mapping
                        break
            
            # Get element dimensions from the prefix mapping if available
            element_width = None
            element_height = None
            
            # If we have an exact prefix match, use its dimensions first
            if exact_prefix_match:
                if 'width' in exact_prefix_match:
                    element_width = exact_prefix_match['width']
                if 'height' in exact_prefix_match:
                    element_height = exact_prefix_match['height']
                debug_buffer.append(f"Using dimensions from prefix mapping '{label_prefix}': {element_width}x{element_height}")
            
            # If no dimensions from prefix mapping, check element_size_mapping
            if element_width is None or element_height is None:
                if 'element_size_mapping' in self.custom_options and svg_type in self.custom_options['element_size_mapping']:
                    size_mapping = self.custom_options['element_size_mapping'][svg_type]
                    if element_width is None and 'width' in size_mapping:
                        element_width = size_mapping['width']
                    if element_height is None and 'height' in size_mapping:
                        element_height = size_mapping['height']
                    debug_buffer.append(f"Using dimensions from element_size_mapping: {element_width}x{element_height}")
            
            # If still no dimensions, try direct custom_options
            if element_width is None:
                element_width = self.custom_options.get('width', 10)
            if element_height is None:
                element_height = self.custom_options.get('height', 10)
            
            debug_buffer.append(f"Final dimensions for {element_name}: {element_width}x{element_height}")
            
            # Initialize final_x and final_y with default values
            final_x = transformed_center_x
            final_y = transformed_center_y
            
            # Handle elements based on their type
            if svg_type == 'path':
                # Special handling for path elements
                
                # Additional debugging for y-coordinate issue
                svg_height = float(self.svg_element.getAttribute('height') or 0)
                debug_buffer.append(f"SVG HEIGHT: {svg_height}")
                
                # Force using original path coordinates option
                use_original_path_coords = self.custom_options.get('use_original_path_coords', False)
                
                if use_original_path_coords:
                    debug_buffer.append(f"USING ORIGINAL PATH COORDINATES - Original: ({orig_center_x}, {orig_center_y})")
                    final_x = orig_center_x
                    final_y = orig_center_y
                else:
                    # Check if y-coordinate seems to be inverted (common in some SVG processing)
                    if svg_height > 0 and abs(svg_height - orig_center_y) < 100:
                        debug_buffer.append(f"POSSIBLE Y-INVERSION DETECTED: SVG height={svg_height}, y-coord={orig_center_y}")
                        debug_buffer.append(f"Testing if y-coordinate is being flipped from bottom-left to top-left origin")
                        
                        # Try using the y-coordinate directly from the path data
                        # without any transformation
                        if 'y_coordinate_handling' in self.custom_options and self.custom_options['y_coordinate_handling'] == 'preserve':
                            debug_buffer.append(f"Using preserve mode for y-coordinate")
                            final_y = orig_center_y
                
                debug_buffer.append(f"Using path coordinates directly: ({final_x}, {final_y})")
                
                # For path elements, explicitly set element_width and element_height to be used for display purposes
                # but they don't affect the positioning
                if exact_prefix_match:
                    if 'width' in exact_prefix_match:
                        element_width = exact_prefix_match['width']
                    if 'height' in exact_prefix_match:
                        element_height = exact_prefix_match['height']
                    debug_buffer.append(f"Using display dimensions for path from mapping: {element_width}x{element_height}")
            else:
                # For non-path elements, calculate the centered position
                final_x = transformed_center_x - element_width / 2
                final_y = transformed_center_y - element_height / 2
                debug_buffer.append(f"Calculated centered position: ({final_x}, {final_y})")
            
            # Apply x_offset and y_offset from mapping if available
            x_offset = 0
            y_offset = 0
            
            # Get x_offset and y_offset from mappings based on svg_type and label_prefix
            if 'element_mappings' in self.custom_options:
                # Find best match (exact match with label prefix first, then fallback to no prefix)
                exact_match = None
                fallback_match = None
                
                for mapping in self.custom_options['element_mappings']:
                    if mapping.get('svg_type', '') == svg_type:
                        if mapping.get('label_prefix', '') == label_prefix:
                            exact_match = mapping
                            break
                        elif not mapping.get('label_prefix', ''):
                            fallback_match = mapping
                
                # Use exact match if found, otherwise use fallback
                mapping_to_use = exact_match or fallback_match
                
                if mapping_to_use:
                    # Get x_offset and y_offset
                    x_offset = mapping_to_use.get('x_offset', 0)
                    y_offset = mapping_to_use.get('y_offset', 0)
                    
            # Apply offsets
            final_x += x_offset
            final_y += y_offset
            
            debug_buffer.append(f"Applied offsets: x_offset={x_offset}, y_offset={y_offset}")
            
            suffix = None
            
            # Check for specific suffixes to override rotation
            if element_name and len(element_name) >= 2:
                last_char = element_name[-1].lower()
                if last_char in ['r', 'd', 'l', 'u']:
                    suffix = last_char
                    # Store original rotation for debug output
                    original_rotation = rotation_angle
                    
                    # Override rotation based on suffix
                    if last_char == 'r':
                        rotation_angle = 0
                    elif last_char == 'd':
                        rotation_angle = 90
                    elif last_char == 'l':
                        rotation_angle = 180
                    elif last_char == 'u':
                        rotation_angle = 270
                    
                    # Log that we're overriding the rotation
                    debug_buffer.append(f"SUFFIX ROTATION OVERRIDE: Suffix '{last_char}' changed rotation from {original_rotation}deg to {rotation_angle}deg")
            
            # Log detailed positioning information for debugging
            debug_buffer.append(f"{svg_type.capitalize()} #{element_count}: {element_name}, " 
                  f"Original center: ({orig_center_x}, {orig_center_y}), "
                  f"Transformed center: ({transformed_center_x}, {transformed_center_y}), "
                  f"Final position: ({final_x}, {final_y}), "
                  f"Using element size: {element_width}x{element_height}, "
                  f"Offsets: (x={x_offset}, y={y_offset}), "
                  f"Rotation: {rotation_angle}deg")
            
            # Clean the element name by removing prefix/suffix AFTER logging
            cleaned_name = self.clean_element_name(
                element_name, 
                label_prefix if label_prefix else None, 
                suffix,
                has_prefix_mapping
            )
            
            # Log information about name cleaning
            if cleaned_name != element_name:
                debug_buffer.append(f"Cleaned element name: '{element_name}' → '{cleaned_name}' [Prefix mapping: {has_prefix_mapping}, Suffix: {suffix}]")
                element_name = cleaned_name
            
            # Now create JSON with element name, position, and other properties
            return self.create_element_json(
                element_name=element_name,
                element_id=element_id,
                element_label=element_label,
                element_count=element_count,
                x=final_x,
                y=final_y,
                svg_type=svg_type,
                label_prefix=label_prefix,
                rotation_angle=rotation_angle,
                element_width=element_width,
                element_height=element_height,
                x_offset=x_offset,
                y_offset=y_offset,
                original_name=original_name,
                debug_buffer=debug_buffer,
                has_prefix_mapping=has_prefix_mapping
            )
        
        except Exception as e:
            print(f"Error processing {svg_type} #{element_count}: {e}")
            import traceback
            traceback.print_exc()
            # Return a default element with error information
            return self.create_default_element(element_count, svg_type, str(e))
    
    def extract_rotation_from_transform(self, element):
        """Extract rotation angle from element's transform attribute if it exists."""
        # Get the transform attribute
        transform_str = element.getAttribute('transform')
        if not transform_str:
            return 0
        
        # First try direct extraction for rotate transform
        direct_rotate = re.search(r'rotate\s*\(\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)', transform_str)
        if direct_rotate:
            try:
                angle = float(direct_rotate.group(1))
                print(f"Directly extracted rotation angle: {angle} degrees")
                return angle
            except Exception as e:
                print(f"Error extracting direct rotation: {e}")
        
        # If no direct rotation found, look at the transform matrix
        try:
            # Get the complete transform matrix for this element (including parent transforms)
            transform_matrix = self.get_all_transforms(element)
            
            # Calculate rotation from matrix - using arctan2 of the matrix elements
            # In SVG transform matrix [a c e; b d f; 0 0 1], rotation is atan2(b, a)
            a = transform_matrix[0, 0]
            b = transform_matrix[1, 0]
            
            # Avoid division by zero
            if abs(a) < 1e-6 and abs(b) < 1e-6:
                return 0
                
            angle_rad = math.atan2(b, a)
            angle_deg = math.degrees(angle_rad)
            
            print(f"Extracted rotation from transform matrix: {angle_deg} degrees")
            
            return angle_deg
            
        except Exception as e:
            print(f"Error calculating rotation from matrix: {e}")
            return 0
    
    def create_default_element(self, element_count, svg_type, error_msg):
        """Create a default element when processing fails."""
        element_name = f"error_{svg_type}{element_count}"
        
        return {
            "type": "ia.display.view",
            "version": 0,
            "props": {
                "path": "Symbol-Views/Equipment-Views/Status",
                "params": {
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
                "originalName": "",
                "elementNumber": element_count,
                "svgType": svg_type,
                "error": error_msg
            },
            "position": {
                "x": 0,
                "y": 0,
                "height": 14,
                "width": 14,
                "rotate": {
                    "anchor": "50% 50%",
                    "angle": "0deg"
                }
            },
            "custom": {}
        }
    
    def process_rectangle(self, rect, rect_count):
        """Process a single rectangle element - for backward compatibility."""
        return self.process_element(rect, rect_count, 'rect')
    
    def process_svg(self):
        """Process SVG file and extract elements with calculated centers."""
        # Results list for all elements
        results = []
        
        # Process different element types
        element_types = [
            ('rect', 'rectangles'),
            ('circle', 'circles'),
            ('ellipse', 'ellipses'),
            ('line', 'lines'),                   
            ('polyline', 'polylines'),
            ('polygon', 'polygons'),
            ('path', 'paths')
        ]
        
        total_elements = 0
        
        # Process each type of element
        for svg_type, plural in element_types:
            elements = self.doc.getElementsByTagName(svg_type)
            count = 0
            
            for element in elements:
                count += 1
                total_elements += 1
                element_json = self.process_element(element, count, svg_type)
                if element_json:
                    results.append(element_json)
            
            if count > 0:
                print(f"Processed {count} {plural}, successfully converted {count}")
        
        print(f"Total: Processed {total_elements} SVG elements, successfully converted {len(results)}")
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
            
            # Handle both old rectNumber and new elementNumber field
            old_number = old_el["meta"].get("rectNumber", old_el["meta"].get("elementNumber", -1))
            new_number = new_el["meta"].get("elementNumber", -1)
            element_num_match = old_number == new_number
            
            # Check tag properties if they exist
            tag_props_match = True
            if "props" in new_el and "props" in old_el:
                if "params" in new_el["props"] and "params" in old_el["props"]:
                    if "tagProps" in new_el["props"]["params"] and "tagProps" in old_el["props"]["params"]:
                        tag_props_match = new_el["props"]["params"]["tagProps"] == old_el["props"]["params"]["tagProps"]
            
            if not (pos_match and name_match and element_num_match and tag_props_match):
                mismatches += 1
                if mismatches <= 5:  # Limit reporting to first 5 mismatches to avoid flooding console
                    print(f"Mismatch at element {idx}:")
                    if not pos_match:
                        print(f"  Position: New ({new_el['position']['x']}, {new_el['position']['y']}) vs "
                              f"Old ({old_el['position']['x']}, {old_el['position']['y']})")
                    if not name_match:
                        print(f"  Name: New '{new_el['meta']['name']}' vs Old '{old_el['meta']['name']}'")
                    if not element_num_match:
                        print(f"  Element Number: New {new_number} vs Old {old_number}")
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