import xml.etree.ElementTree as ET
import json
import re
import math
import numpy as np
import os
import argparse
import logging
import sys
from xml.dom import minidom

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Add stdout handler for UI capture
        logging.StreamHandler()             # Keep default stderr handler
    ]
)
logger = logging.getLogger('svg_transformer')

# Add UI-compatible print function
def ui_print(message, level=logging.INFO):
    """Print a message to both the logger and stdout for UI capture."""
    logger.log(level, message)
    # Also print to stdout directly for UIs that capture print statements
    print(message)
    
    # Ensure the message is immediately displayed
    sys.stdout.flush()

class SVGTransformer:
    """Class to handle SVG parsing and transformation of SVG elements."""
    
    def __init__(self, svg_path, custom_options=None, debug=False):
        """Initialize with the path to the SVG file and optional custom options."""
        self.svg_path = svg_path
        self.doc = minidom.parse(svg_path)
        self.svg_element = self.doc.getElementsByTagName('svg')[0]
        self.custom_options = custom_options or {}
        self.debug = debug
        
        # Set logging level based on debug flag
        if self.debug:
            logger.setLevel(logging.DEBUG)
        
        # Debug print the custom_options
        ui_print("DEBUG: Loaded custom_options:")
        if 'element_mappings' in self.custom_options:
            ui_print(f"DEBUG: Found {len(self.custom_options['element_mappings'])} element mappings")
            for i, mapping in enumerate(self.custom_options['element_mappings']):
                ui_print(f"DEBUG: Mapping #{i+1}: svg_type='{mapping.get('svg_type')}', label_prefix='{mapping.get('label_prefix')}', props_path='{mapping.get('props_path')}'")
        else:
            ui_print("DEBUG: No element_mappings found in custom_options")
        
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
                    logger.error(f"Error parsing transform parameters '{params_str}': {e}")
                    # Continue with the current matrix rather than failing
        except Exception as e:
            logger.error(f"Error parsing transform '{transform_str}': {e}")
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
        if self.debug:
            logger.debug(f"Applying transform to point {point} with matrix {transform_matrix} → result: ({transformed[0]}, {transformed[1]})")
        
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
        
        logger.debug(f"Looking for mapping for svg_type={svg_type}, label_prefix='{label_prefix}'")
        
        # First pass: look for an exact match
        if label_prefix:  # Only look for exact match if we have a prefix
            for mapping in self.custom_options['element_mappings']:
                if mapping['svg_type'] == svg_type and mapping.get('label_prefix', '') == label_prefix:
                    exact_match = mapping
                    logger.debug(f"Found exact match: {mapping}")
                    break
        
        # Second pass: look for a fallback match (no prefix)
        for mapping in self.custom_options['element_mappings']:
            if mapping['svg_type'] == svg_type and not mapping.get('label_prefix', ''):
                fallback_match = mapping
                logger.debug(f"Found fallback match: {mapping}")
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
        # If not provided, element_width and element_height should be retrieved from custom_options
        if element_width is None:
            element_width = self.custom_options.get('width', 10)
            if self.debug:
                logger.debug(f"Using fallback width: {element_width}")
        if element_height is None:
            element_height = self.custom_options.get('height', 10)
            if self.debug:
                logger.debug(f"Using fallback height: {element_height}")
            
        # Store debug buffer contents if provided
        debug_messages = []
        if debug_buffer is not None:
            debug_messages = debug_buffer.copy()
            
        # Log all debug messages to the console for transparency
        if self.debug:
            for msg in debug_messages:
                logger.debug(msg)
            
            logger.debug("==== END DEBUG ====")
        
        # Get the appropriate element type and props path based on prefix
        # First look for an exact match with this prefix
        exact_match = None
        fallback_match = None
        
        logger.debug(f"Looking for mapping for svg_type={svg_type}, label_prefix='{label_prefix}'")
        logger.debug(f"Available mappings: {len(self.custom_options.get('element_mappings', []))}")
        
        # Debug print all available mappings
        if self.debug:
            for i, mapping in enumerate(self.custom_options.get('element_mappings', [])):
                logger.debug(f"  Available mapping #{i+1}: svg_type={mapping.get('svg_type', 'None')}, label_prefix='{mapping.get('label_prefix', '')}'")
        
        if 'element_mappings' in self.custom_options and label_prefix:
            for mapping in self.custom_options['element_mappings']:
                if mapping.get('svg_type', '') == svg_type and mapping.get('label_prefix', '') == label_prefix:
                    exact_match = mapping
                    logger.debug(f"Found exact match: {mapping}")
                    break
        
        # Then look for a fallback with no prefix
        for mapping in self.custom_options.get('element_mappings', []):
            if mapping['svg_type'] == svg_type and not mapping.get('label_prefix', ''):
                fallback_match = mapping
                if not exact_match:  # Only print if we haven't found an exact match
                    logger.debug(f"Found fallback match: {mapping}")
                break
        
        # Use the appropriate mapping
        mapping_to_use = exact_match or fallback_match
        
        # Get element type and props path from mapping
        element_type = "ia.display.view"  # Default
        props_path = "Symbol-Views/Equipment-Views/Status"  # Default
        
        if mapping_to_use:
            element_type = mapping_to_use.get('element_type', element_type)
            props_path = mapping_to_use.get('props_path', props_path)
            logger.debug(f"Selected mapping: {mapping_to_use}")
            logger.debug(f"Using element_type: {element_type} from {'exact match' if exact_match else 'fallback match'}")
            logger.debug(f"Using props_path: {props_path} from {'exact match' if exact_match else 'fallback match'}")
        else:
            warning_msg = f"WARNING: No mapping found for svg_type={svg_type}, label_prefix='{label_prefix}'. Using defaults: type={element_type}, props={props_path}"
            logger.warning(warning_msg)
            # Only display in UI for specific types or when in debug mode to avoid flooding
            if self.debug or svg_type in ['rect', 'path'] and not label_prefix:
                ui_print(warning_msg, logging.WARNING)
        
        # Preserve rotation angle as float for accuracy, just format it for output
        try:
            rotation_angle = float(rotation_angle)
        except (ValueError, TypeError):
            rotation_angle = 0
        
        # Create metadata and meta object
        meta = {
            'id': element_id,
            'name': element_name,
            'originalName': original_name or element_name,  # Preserve original name
            'elementPrefix': label_prefix if label_prefix else None
        }
        
        # CRITICAL: If we're using a mapping with a final_prefix, we need to ensure
        # we're setting the elementPrefix appropriately
        if mapping_to_use:
            final_prefix = mapping_to_use.get('final_prefix', '')
            final_suffix = mapping_to_use.get('final_suffix', '')
            
            if final_prefix:
                meta['finalPrefixApplied'] = final_prefix
                # If we're applying a final prefix, we should ensure elementPrefix reflects this
                if not meta['elementPrefix']:
                    meta['elementPrefix'] = mapping_to_use.get('label_prefix', '')
                    if self.debug:
                        logger.debug(f"Setting elementPrefix to '{meta['elementPrefix']}' based on mapping that provided final_prefix")
            
            if final_suffix:
                meta['finalSuffixApplied'] = final_suffix
        
        # Build the element JSON object with the simpler position structure
        element_json = {
            'type': element_type,
            'version': 0,
            'props': {
                'path': props_path
            },
            'meta': meta,
            'position': {
                'x': x,
                'y': y,
                'width': element_width,
                'height': element_height
            },
            'custom': {}
        }
        
        # Add rotation if it's not 0
        if rotation_angle != 0:
            element_json['position']['rotate'] = {
                'angle': f"{rotation_angle}deg",
                'anchor': '50% 50%'
            }
        
        return element_json
    
    def clean_element_name(self, element_name, prefix=None, suffix=None, has_prefix_mapping=False, mapping_to_use=None):
        """Clean element name by removing prefix and suffix if configured.
        Also removes adjacent underscores.
        
        Args:
            element_name (str): Original element name
            prefix (str): Identified prefix to remove (if any)
            suffix (str): Identified suffix to remove (if any)
            has_prefix_mapping (bool): Whether a mapping exists for the prefix
            mapping_to_use (dict): The mapping being used for this element (if any)
            
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
            cleaned_name = element_name
        
        # Apply final prefix and suffix if they exist in the mapping
        if mapping_to_use:
            # Apply final prefix if it exists in the mapping
            final_prefix = mapping_to_use.get('final_prefix', '')
            if final_prefix:
                # Ensure final prefix is followed by an underscore
                if not final_prefix.endswith('_'):
                    final_prefix += '_'
                cleaned_name = f"{final_prefix}{cleaned_name}"
            
            # Apply final suffix if it exists in the mapping
            final_suffix = mapping_to_use.get('final_suffix', '')
            if final_suffix:
                # Ensure final suffix is preceded by an underscore
                if not final_suffix.startswith('_'):
                    final_suffix = f"_{final_suffix}"
                cleaned_name = f"{cleaned_name}{final_suffix}"
            
        return cleaned_name
    
    def process_element(self, element, element_count, svg_type):
        """Process a single SVG element and return its JSON representation."""
        try:
            debug_buffer = []  # Collect debug messages
            
            if self.debug:
                logger.debug(f"Processing {svg_type} #{element_count}")
                debug_buffer.append(f"Processing {svg_type} #{element_count}")
            
            # Initialize transformed coordinates
            transformed_center_x = 0
            transformed_center_y = 0
            
            # Get element name from ID or create a default one
            element_id = element.getAttribute('id') or ""
            element_label = element.getAttribute('inkscape:label') or element_id  # Use ID as fallback for label
            element_name = element_label or f"{svg_type}{element_count}"
            original_name = element_name  # Store original name
            
            # Get the prefix from the label (text before underscore)
            candidate_prefix = ""
            if element_label and "_" in element_label:
                candidate_prefix = element_label.split("_")[0]
            
            # Only treat it as a prefix if it exists in the mappings
            label_prefix = ""
            if 'element_mappings' in self.custom_options and candidate_prefix:
                prefix_exists = False
                for mapping in self.custom_options['element_mappings']:
                    # Case-insensitive comparison
                    if mapping.get('label_prefix', '').upper() == candidate_prefix.upper():
                        prefix_exists = True
                        # Use the prefix as defined in the mapping (preserve case from mapping)
                        label_prefix = mapping.get('label_prefix', '')
                        break
                
                # Only use the prefix if it's defined in the mappings
                if prefix_exists:
                    logger.debug(f"Found valid prefix '{label_prefix}' in mappings for element {element_label}")
                else:
                    logger.debug(f"Extracted prefix '{candidate_prefix}' not found in mappings, treating as no prefix")
            
            if self.debug:
                logger.debug(f"Final label_prefix for {element_label}: '{label_prefix}'")
            
            # Get original element coordinates and dimensions
            # Process based on element type
            orig_center_x = 0
            orig_center_y = 0
            
            # Try to get original width and height for appropriate element types
            element_width = None
            element_height = None
            
            if self.debug:
                logger.debug(f"Processing element: {element_name} (SVG type: {svg_type})")
            
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
                        logger.debug(f"Processing path with data: {d_attr}")
                        
                        # For special debugging
                        logger.debug(f"*** Y-COORDINATE DEBUG ***")
                        
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
                            logger.debug(f"Found comma-separated coordinates")
                        elif space_separated:
                            logger.debug(f"Found space-separated coordinates")
                        else:
                            logger.debug(f"Could not find coordinates with standard patterns")
                        
                        # Determine if we're using relative coordinates (lowercase 'm' means relative)
                        is_relative = d_attr.strip().startswith('m')
                        
                        if path_coords:
                            try:
                                # Extract the raw coordinate values from the path data
                                x_str = path_coords[0][0]
                                y_str = path_coords[0][1]
                                
                                logger.debug(f"Raw extracted values - x_str: '{x_str}', y_str: '{y_str}'")
                                
                                # Convert to float
                                orig_center_x = float(x_str)
                                orig_center_y = float(y_str)
                                
                                logger.debug(f"After float conversion - x: {orig_center_x}, y: {orig_center_y}")
                                logger.debug(f"Extracted path starting coordinates: ({orig_center_x}, {orig_center_y}) - {'Relative' if is_relative else 'Absolute'} coordinates")
                            except (ValueError, IndexError) as e:
                                logger.debug(f"Error extracting path coordinates: {e}")
                        else:
                            logger.debug(f"Could not extract coordinates from path data: {d_attr}")
                
                logger.debug(f"Warning: {svg_type} element support is basic - center may not be accurate")
            else:
                # Default case for unsupported types
                orig_center_x, orig_center_y = 0, 0
                original_width = 10  # Default
                original_height = 10  # Default
                logger.debug(f"Warning: Unsupported element type {svg_type}")
            
            # Get transformation matrix from all parent transforms
            transform_matrix = self.get_all_transforms(element)
            
            # Print the original transform string for debugging
            transform_str = element.getAttribute('transform')
            if transform_str:
                logger.debug(f"Element has transform: {transform_str}")
            
            # Extract rotation angle from the transform
            rotation_angle = self.extract_rotation_from_transform(element)
            
            # Apply transform to the center point to get transformed center
            transformed_center_x, transformed_center_y = self.apply_transform(
                (orig_center_x, orig_center_y), transform_matrix
            )
            
            # For debugging - print transformation details for path elements
            if svg_type == 'path':
                logger.debug(f"TRANSFORM DEBUG - Original: ({orig_center_x}, {orig_center_y}), Transformed: ({transformed_center_x}, {transformed_center_y})")
                
                # Print transform matrix if available
                if transform_matrix is not None and not np.array_equal(transform_matrix, np.identity(3)):
                    logger.debug(f"Transform Matrix: {transform_matrix}")
            
            # Get element identifiers - this section is duplicated, let's remove it 
            # element_id = element.getAttribute('id') or ""
            # element_label = element.getAttribute('inkscape:label') or ""
            # element_name = element_label or f"{svg_type}{element_count}"
            # original_name = element_name  # Store original name
            
            # Get the prefix from the label (text before underscore)
            # label_prefix = ""
            # if element_label and "_" in element_label:
            #     label_prefix = element_label.split("_")[0]
            
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
                logger.debug(f"Using dimensions from prefix mapping '{label_prefix}': {element_width}x{element_height}")
            
            # Get size mapping based on element type
            if element_width is None or element_height is None:
                if 'element_size_mapping' in self.custom_options and svg_type in self.custom_options['element_size_mapping']:
                    size_mapping = self.custom_options['element_size_mapping'][svg_type]
                    if element_width is None and 'width' in size_mapping:
                        element_width = size_mapping['width']
                    if element_height is None and 'height' in size_mapping:
                        element_height = size_mapping['height']
                    logger.debug(f"Using dimensions from element_size_mapping: {element_width}x{element_height}")
                    logger.debug(f"DEBUG: Using size mapping for {svg_type}: width={element_width}, height={element_height}")
            
            # If still no dimensions, try direct custom_options
            if element_width is None:
                element_width = self.custom_options.get('width', 10)
                logger.debug(f"DEBUG: Using fallback width: {element_width}")
            if element_height is None:
                element_height = self.custom_options.get('height', 10)
                logger.debug(f"DEBUG: Using fallback height: {element_height}")
            
            logger.debug(f"Final dimensions for {element_name}: {element_width}x{element_height}")
            logger.debug(f"DEBUG: Final dimensions for {element_name}: {element_width}x{element_height}")
            
            # Initialize final_x and final_y with default values
            final_x = transformed_center_x
            final_y = transformed_center_y
            
            # Handle elements based on their type
            if svg_type == 'path':
                # Special handling for path elements
                
                # Additional debugging for y-coordinate issue
                svg_height = float(self.svg_element.getAttribute('height') or 0)
                logger.debug(f"SVG HEIGHT: {svg_height}")
                
                # Force using original path coordinates option
                use_original_path_coords = self.custom_options.get('use_original_path_coords', False)
                
                if use_original_path_coords:
                    logger.debug(f"USING ORIGINAL PATH COORDINATES - Original: ({orig_center_x}, {orig_center_y})")
                    final_x = orig_center_x
                    final_y = orig_center_y
                else:
                    # Check if y-coordinate seems to be inverted (common in some SVG processing)
                    if svg_height > 0 and abs(svg_height - orig_center_y) < 100:
                        logger.debug(f"POSSIBLE Y-INVERSION DETECTED: SVG height={svg_height}, y-coord={orig_center_y}")
                        logger.debug(f"Testing if y-coordinate is being flipped from bottom-left to top-left origin")
                        
                        # Try using the y-coordinate directly from the path data
                        # without any transformation
                        if 'y_coordinate_handling' in self.custom_options and self.custom_options['y_coordinate_handling'] == 'preserve':
                            logger.debug(f"Using preserve mode for y-coordinate")
                            final_y = orig_center_y
                
                logger.debug(f"Using path coordinates directly: ({final_x}, {final_y})")
                
                # For path elements, explicitly set element_width and element_height to be used for display purposes
                # but they don't affect the positioning
                if exact_prefix_match:
                    if 'width' in exact_prefix_match:
                        element_width = exact_prefix_match['width']
                    if 'height' in exact_prefix_match:
                        element_height = exact_prefix_match['height']
                    logger.debug(f"Using display dimensions for path from mapping: {element_width}x{element_height}")
            else:
                # For non-path elements, calculate the centered position
                final_x = transformed_center_x - element_width / 2
                final_y = transformed_center_y - element_height / 2
                logger.debug(f"Calculated centered position: ({final_x}, {final_y})")
            
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
            else:
                # Initialize mapping_to_use to None if 'element_mappings' is not in custom_options
                mapping_to_use = None
                    
            # Apply offsets
            final_x += x_offset
            final_y += y_offset
            
            logger.debug(f"Applied offsets: x_offset={x_offset}, y_offset={y_offset}")
            
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
                    logger.debug(f"SUFFIX ROTATION OVERRIDE: Suffix '{last_char}' changed rotation from {original_rotation}deg to {rotation_angle}deg")
            
            # Log detailed positioning information for debugging
            logger.debug(f"{svg_type.capitalize()} #{element_count}: {element_name}, " 
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
                has_prefix_mapping,
                mapping_to_use
            )
            
            # Log information about name cleaning
            if cleaned_name != element_name:
                logger.debug(f"Cleaned element name: '{element_name}' → '{cleaned_name}' [Prefix mapping: {has_prefix_mapping}, Suffix: {suffix}]")
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
            logger.error(f"DEBUG ERROR: Failed to process element {element_count} of type {svg_type}: {str(e)}")
            import traceback
            traceback.print_exc()
            # Create a default element when there's an error
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
                logger.debug(f"Directly extracted rotation angle: {angle} degrees")
                return angle
            except Exception as e:
                logger.error(f"Error extracting direct rotation: {e}")
        
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
            
            logger.debug(f"Extracted rotation from transform matrix: {angle_deg} degrees")
            
            return angle_deg
            
        except Exception as e:
            logger.error(f"Error calculating rotation from matrix: {e}")
            return 0
    
    def create_default_element(self, element_count, svg_type, error_msg):
        """Create a default element when processing fails."""
        element_name = f"error_{svg_type}{element_count}"
        
        logger.debug(f"DEBUG: Creating default element due to error: {error_msg}")
        logger.debug(f"DEBUG: Default element name: {element_name}, type: {svg_type}")
        
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
        processed_elements = 0
        
        # Process each type of element that are direct children of the SVG (not in groups)
        for svg_type, plural in element_types:
            elements = self.doc.getElementsByTagName(svg_type)
            count = 0
            
            for element in elements:
                # Only process elements that are direct children of the SVG (not in groups)
                # Check if the parent is not a group element
                if element.parentNode.tagName != 'g':
                    count += 1
                    total_elements += 1
                    element_json = self.process_element(element, count, svg_type)
                    if element_json:
                        results.append(element_json)
                        processed_elements += 1
            
            if count > 0:
                logger.info(f"Processed {count} {plural} (outside groups), successfully converted {count}")
                ui_print(f"Processed {count} {plural} (outside groups), successfully converted {count}")
        
        # Process group elements
        groups = self.doc.getElementsByTagName('g')
        group_count = 0
        
        for group in groups:
            group_count += 1
            group_elements = self.process_group(group, group_count)
            if group_elements:
                results.extend(group_elements)
                total_elements += len(group_elements)
                processed_elements += len(group_elements)
                logger.info(f"Processed group #{group_count} with {len(group_elements)} elements")
                ui_print(f"Processed group #{group_count} with {len(group_elements)} elements")
        
        logger.info(f"Total: Processed {total_elements} SVG elements ({group_count} groups), successfully converted {processed_elements}")
        ui_print(f"Total: Processed {total_elements} SVG elements ({group_count} groups), successfully converted {processed_elements}")
        return results
    
    def process_group(self, group, group_count):
        """Process a group element and all its children."""
        results = []
        
        # Get group attributes
        group_id = group.getAttribute('id') or f"group{group_count}"
        group_label = group.getAttribute('inkscape:label') or ""
        
        ui_print(f"DEBUG: Raw group info: id='{group_id}', label='{group_label}'")
        
        # Extract group label prefix (if any)
        group_label_prefix = ""
        if group_label and "_" in group_label:
            group_label_prefix = group_label.split("_")[0]
            ui_print(f"DEBUG: Group #{group_count} has label with underscore, extracted prefix: '{group_label_prefix}'")
        # If no prefix from label with underscore, check if the label itself matches a mapping prefix
        elif group_label:
            # Check if the group label itself exists as a label_prefix in mappings
            ui_print(f"DEBUG: Group #{group_count} has no label with underscore, checking if group label '{group_label}' matches any mapping prefixes")
            if 'element_mappings' in self.custom_options:
                # First try exact match
                has_exact_match = False
                for mapping in self.custom_options['element_mappings']:
                    if mapping.get('label_prefix', '') == group_label:
                        group_label_prefix = group_label
                        ui_print(f"DEBUG: Found exact match for group label '{group_label}' as prefix")
                        has_exact_match = True
                        break
                
                # If no exact match, try case-insensitive match
                if not has_exact_match:
                    ui_print(f"DEBUG: No exact match for group label '{group_label}', trying case-insensitive match")
                    for mapping in self.custom_options['element_mappings']:
                        # Case-insensitive comparison
                        ui_print(f"DEBUG: Comparing group label '{group_label.upper()}' with mapping prefix '{mapping.get('label_prefix', '').upper()}'")
                        if mapping.get('label_prefix', '').upper() == group_label.upper():
                            group_label_prefix = mapping.get('label_prefix', '')
                            ui_print(f"DEBUG: Using group label '{group_label}' as prefix '{group_label_prefix}' (matched mapping case-insensitively)")
                            break
        
        # If still no prefix, try to use the group ID as a fallback
        if not group_label_prefix and group_id:
            # Check if group ID exists as a label_prefix in mappings
            ui_print(f"DEBUG: Group #{group_count} has no label prefix, checking if group ID '{group_id}' matches any mapping prefixes")
            if 'element_mappings' in self.custom_options:
                # First try exact match
                has_exact_match = False
                for mapping in self.custom_options['element_mappings']:
                    if mapping.get('label_prefix', '') == group_id:
                        group_label_prefix = group_id
                        ui_print(f"DEBUG: Found exact match for group ID '{group_id}' as prefix")
                        has_exact_match = True
                        break
                
                # If no exact match, try case-insensitive match
                if not has_exact_match:
                    ui_print(f"DEBUG: No exact match for group ID '{group_id}', trying case-insensitive match")
                    for mapping in self.custom_options['element_mappings']:
                        # Case-insensitive comparison
                        ui_print(f"DEBUG: Comparing group ID '{group_id.upper()}' with mapping prefix '{mapping.get('label_prefix', '').upper()}'")
                        if mapping.get('label_prefix', '').upper() == group_id.upper():
                            group_label_prefix = mapping.get('label_prefix', '')
                            ui_print(f"DEBUG: Using group ID '{group_id}' as prefix '{group_label_prefix}' (matched mapping case-insensitively)")
                            break
        
        # Extract group suffix (if any)
        group_suffix = None
        if group_label and len(group_label) >= 2:
            last_char = group_label[-1].lower()
            if last_char in ['r', 'd', 'l', 'u']:
                group_suffix = last_char
                ui_print(f"DEBUG: Group #{group_count} has suffix: '{group_suffix}'")
        
        # Standard debugging for all groups
        ui_print(f"PROCESSING GROUP: #{group_count}: id='{group_id}', label='{group_label}', prefix='{group_label_prefix}', suffix='{group_suffix}'")
        
        # Get all child elements of supported types
        element_types = ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path']
        element_count_by_type = {svg_type: 0 for svg_type in element_types}
        
        # Process direct children of this group
        for child in group.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
                
            svg_type = child.tagName
            if svg_type in element_types:
                # Increment count for this type
                element_count_by_type[svg_type] += 1
                count = element_count_by_type[svg_type]
                
                # Get element details for debugging
                element_id = child.getAttribute('id') or ""
                element_label = child.getAttribute('inkscape:label') or element_id
                ui_print(f"DEBUG: Processing element in group '{group_id}': id='{element_id}', label='{element_label}', type='{svg_type}'")
                
                # Process the element
                element_json = self.process_element_with_group_context(
                    child, 
                    count, 
                    svg_type, 
                    group_label_prefix, 
                    group_suffix
                )
                
                if element_json:
                    results.append(element_json)
                    ui_print(f"DEBUG: Element '{element_label}' final processing result: props_path='{element_json['props']['path']}', elementPrefix='{element_json['meta'].get('elementPrefix')}'")
                else:
                    ui_print(f"DEBUG: Element '{element_label}' processing failed, no JSON returned")
        
        return results
    
    def process_element_with_group_context(self, element, element_count, svg_type, group_label_prefix, group_suffix):
        """Process an element within a group context, applying group prefix/suffix if appropriate."""
        try:
            # Get the element's own attributes
            element_id = element.getAttribute('id') or ""
            element_label = element.getAttribute('inkscape:label') or element_id  # Use ID as fallback for label
            
            ui_print(f"GROUP CONTEXT PROCESSING: element '{element_label}' (type={svg_type}) with group_prefix='{group_label_prefix}'")
            
            # Check if the element has its own suffix
            has_own_suffix = False
            if element_label and len(element_label) >= 2:
                last_char = element_label[-1].lower()
                if last_char in ['r', 'd', 'l', 'u']:
                    has_own_suffix = True
                    ui_print(f"DEBUG: Element '{element_label}' has its own suffix: '{last_char}'")
            
            # Check if the element has its own prefix
            has_own_prefix = False
            element_prefix = ""
            if element_label and "_" in element_label:
                candidate_prefix = element_label.split("_")[0]
                ui_print(f"DEBUG: Element '{element_label}' has underscore, candidate prefix: '{candidate_prefix}'")
                
                # Only treat it as a prefix if it exists in the mappings
                if 'element_mappings' in self.custom_options and candidate_prefix:
                    ui_print(f"DEBUG: Checking if candidate prefix '{candidate_prefix}' exists in mappings")
                    prefix_exists = False
                    for mapping in self.custom_options['element_mappings']:
                        # Case-insensitive comparison
                        ui_print(f"DEBUG: Comparing '{candidate_prefix.upper()}' with '{mapping.get('label_prefix', '').upper()}'")
                        if mapping.get('label_prefix', '').upper() == candidate_prefix.upper():
                            prefix_exists = True
                            # Use the prefix as defined in the mapping (preserve case from mapping)
                            element_prefix = mapping.get('label_prefix', '')
                            ui_print(f"DEBUG: Found valid prefix match: '{element_prefix}' for candidate '{candidate_prefix}'")
                            break
                    
                    # Only use the prefix if it's defined in the mappings
                    if prefix_exists:
                        has_own_prefix = True
                        ui_print(f"DEBUG: Element '{element_label}' has valid own prefix: '{element_prefix}'")
                    else:
                        ui_print(f"DEBUG: Extracted prefix '{candidate_prefix}' not found in mappings, treating as no prefix")
            
            # Important priority decision: If element has no valid prefix but is in a group with prefix,
            # use the group's prefix for processing
            if not has_own_prefix and group_label_prefix:
                ui_print(f"DEBUG: Element '{element_label}' has no valid prefix but is in group with prefix '{group_label_prefix}' - using group prefix")
                
                # Process the element with the group's prefix
                element_json = self.process_element_with_forced_prefix(element, element_count, svg_type, group_label_prefix)
                
                # Add indicator for debugging
                if element_json:
                    element_json['meta']['inheritedGroupPrefix'] = group_label_prefix
                    ui_print(f"INHERITED PREFIX: Applied group prefix '{group_label_prefix}' to element {element_json['meta']['name']}")
                    ui_print(f"DEBUG: Element JSON after forced prefix: props_path='{element_json['props']['path']}', meta={element_json['meta']}")
                    
                    # Apply group suffix if applicable
                    if group_suffix and not has_own_suffix:
                        self.apply_group_suffix(element_json, group_suffix)
                        ui_print(f"DEBUG: Applied group suffix '{group_suffix}' to element {element_json['meta']['name']}")
                    
                    return element_json
                else:
                    ui_print(f"DEBUG: Failed to process element '{element_label}' with forced prefix '{group_label_prefix}'")
                    return None
            
            # If element has its own valid prefix or no group prefix exists, process normally
            ui_print(f"DEBUG: Element '{element_label}' using standard processing (has_own_prefix={has_own_prefix}, group_prefix='{group_label_prefix}')")
            element_json = self.process_element(element, element_count, svg_type)
            if not element_json:
                ui_print(f"DEBUG: Failed to process element '{element_label}' with standard processing")
                return None
            
            # For elements with their own prefix but no suffix, apply group suffix if available
            if group_suffix and not has_own_suffix:
                self.apply_group_suffix(element_json, group_suffix)
                ui_print(f"DEBUG: Applied group suffix '{group_suffix}' to element with own prefix {element_json['meta']['name']}")
            
            return element_json
            
        except Exception as e:
            logger.error(f"Error processing {svg_type} #{element_count} in group context: {e}")
            import traceback
            traceback.print_exc()
            return self.create_default_element(element_count, svg_type, str(e))
    
    def process_element_with_forced_prefix(self, element, element_count, svg_type, forced_prefix):
        """Process an element using a forced prefix for mapping lookup."""
        try:
            # This is a simplified version of process_element that uses the forced prefix
            element_id = element.getAttribute('id') or ""
            element_label = element.getAttribute('inkscape:label') or element_id
            element_name = element_label or f"{svg_type}{element_count}"
            original_name = element_name
            
            ui_print(f"FORCED PREFIX PROCESSING: element '{element_name}' with forced_prefix='{forced_prefix}'")
            
            # CRITICAL CHANGE: Instead of using process_element and then overriding,
            # we'll directly create the element JSON with the forced prefix
            # This avoids any fallback to empty prefix mappings
            
            # Get necessary element geometry and properties, similar to process_element
            # but without the prefix logic
            element_geometry = self.get_element_geometry(element, svg_type)
            rotation_angle = self.extract_rotation_from_transform(element)
            
            # Find the mapping for this forced prefix directly
            # Use case-insensitive comparison for the prefix
            ui_print(f"DEBUG: Searching for mapping with svg_type='{svg_type}' and label_prefix='{forced_prefix}' (case-insensitive)")
            mapping = None
            
            # Debug: Print all available mappings for this SVG type for comparison
            ui_print(f"DEBUG: Available mappings for svg_type='{svg_type}':")
            for i, m in enumerate(self.custom_options.get('element_mappings', [])):
                if m.get('svg_type', '') == svg_type:
                    ui_print(f"DEBUG: Mapping #{i+1}: label_prefix='{m.get('label_prefix', '')}', props_path='{m.get('props_path', '')}'")
            
            for m in self.custom_options.get('element_mappings', []):
                if (m.get('svg_type', '') == svg_type):
                    ui_print(f"DEBUG: Comparing mapping prefix '{m.get('label_prefix', '')}' ({m.get('label_prefix', '').upper()}) with forced prefix '{forced_prefix}' ({forced_prefix.upper()})")
                    if m.get('label_prefix', '').upper() == forced_prefix.upper():
                        mapping = m
                        ui_print(f"DEBUG: FOUND MAPPING with matching prefix: svg_type='{m.get('svg_type')}', label_prefix='{m.get('label_prefix')}', props_path='{m.get('props_path')}'")
                        break
            
            if mapping:
                ui_print(f"DEBUG: Using mapping with props_path='{mapping.get('props_path')}', width={mapping.get('width')}, height={mapping.get('height')}")
                
                # Get dimensions from the mapping
                element_width = mapping.get('width', self.custom_options.get('width', 10))
                element_height = mapping.get('height', self.custom_options.get('height', 10))
                
                # Get offsets from the mapping
                x_offset = mapping.get('x_offset', 0)
                y_offset = mapping.get('y_offset', 0)
                
                # Calculate final position
                if svg_type == 'path':
                    final_x = element_geometry['center_x'] + x_offset
                    final_y = element_geometry['center_y'] + y_offset
                else:
                    final_x = element_geometry['center_x'] - element_width/2 + x_offset
                    final_y = element_geometry['center_y'] - element_height/2 + y_offset
                
                # Handle suffix rotation
                suffix = None
                if element_name and len(element_name) >= 2:
                    last_char = element_name[-1].lower()
                    if last_char in ['r', 'd', 'l', 'u']:
                        suffix = last_char
                        # Override rotation based on suffix
                        if last_char == 'r':
                            rotation_angle = 0
                        elif last_char == 'd':
                            rotation_angle = 90
                        elif last_char == 'l':
                            rotation_angle = 180
                        elif last_char == 'u':
                            rotation_angle = 270
                
                # Clean the element name
                has_prefix_mapping = True  # We know the mapping exists since we found it
                cleaned_name = self.clean_element_name(
                    element_name,
                    mapping.get('label_prefix', ''),  # Use the exact mapped prefix for cleaning
                    suffix,
                    has_prefix_mapping,
                    mapping
                )
                
                ui_print(f"DEBUG: After name cleaning: '{element_name}' -> '{cleaned_name}'")
                
                # Create the element JSON directly with the forced prefix
                ui_print(f"DEBUG: Creating element JSON with label_prefix='{mapping.get('label_prefix', '')}'")
                element_json = self.create_element_json(
                    element_name=cleaned_name,
                    element_id=element_id,
                    element_label=element_label,
                    element_count=element_count,
                    x=final_x,
                    y=final_y,
                    svg_type=svg_type,
                    label_prefix=mapping.get('label_prefix', ''),  # Use the EXACT prefix from the mapping
                    rotation_angle=rotation_angle,
                    element_width=element_width,
                    element_height=element_height,
                    x_offset=x_offset,
                    y_offset=y_offset,
                    original_name=original_name,
                    has_prefix_mapping=has_prefix_mapping
                )
                
                # Add metadata to indicate this was processed with a forced prefix
                element_json['meta']['forcedPrefix'] = forced_prefix
                if forced_prefix.upper() != mapping.get('label_prefix', '').upper():
                    element_json['meta']['mappedPrefix'] = mapping.get('label_prefix', '')
                    
                # CRITICAL: Ensure the elementPrefix is set to the actual prefix from the mapping
                element_json['meta']['elementPrefix'] = mapping.get('label_prefix', '')
                
                ui_print(f"FORCED PREFIX RESULT: element '{element_name}' -> '{cleaned_name}'")
                ui_print(f"  → Using props path: {element_json['props']['path']}")
                ui_print(f"  → Element prefix set to: {element_json['meta']['elementPrefix']}")
                ui_print(f"  → Element dimensions: {element_width}x{element_height}")
                
                return element_json
            else:
                # If no mapping found for the forced prefix, fall back to regular processing
                # but log a warning
                ui_print(f"WARNING: No mapping found for svg_type={svg_type}, forced_prefix='{forced_prefix}' (case-insensitive). Using default processing.")
                ui_print(f"DEBUG: Available mappings in custom_options: {len(self.custom_options.get('element_mappings', []))}")
                for i, m in enumerate(self.custom_options.get('element_mappings', [])):
                    ui_print(f"DEBUG: Mapping #{i+1}: svg_type='{m.get('svg_type', '')}', label_prefix='{m.get('label_prefix', '')}'")
                
                return self.process_element(element, element_count, svg_type)
            
        except Exception as e:
            logger.error(f"Error in process_element_with_forced_prefix: {e}")
            import traceback
            traceback.print_exc()
            return self.process_element(element, element_count, svg_type)
            
    def get_element_geometry(self, element, svg_type):
        """Extract geometry information from an SVG element."""
        geometry = {
            'center_x': 0,
            'center_y': 0,
            'width': 0,
            'height': 0
        }
        
        # Process based on element type
        if svg_type == 'rect':
            x = float(element.getAttribute('x') or 0)
            y = float(element.getAttribute('y') or 0)
            width = float(element.getAttribute('width') or 0)
            height = float(element.getAttribute('height') or 0)
            # Calculate center of the original rect
            geometry['center_x'] = x + width/2
            geometry['center_y'] = y + height/2
            geometry['width'] = width
            geometry['height'] = height
        elif svg_type == 'circle':
            cx = float(element.getAttribute('cx') or 0)
            cy = float(element.getAttribute('cy') or 0)
            r = float(element.getAttribute('r') or 0)
            # The center is already given for circles
            geometry['center_x'] = cx
            geometry['center_y'] = cy
            geometry['width'] = r * 2
            geometry['height'] = r * 2
        elif svg_type == 'ellipse':
            cx = float(element.getAttribute('cx') or 0)
            cy = float(element.getAttribute('cy') or 0)
            rx = float(element.getAttribute('rx') or 0)
            ry = float(element.getAttribute('ry') or 0)
            # The center is already given for ellipses
            geometry['center_x'] = cx
            geometry['center_y'] = cy
            geometry['width'] = rx * 2
            geometry['height'] = ry * 2
        elif svg_type == 'line':
            x1 = float(element.getAttribute('x1') or 0)
            y1 = float(element.getAttribute('y1') or 0)
            x2 = float(element.getAttribute('x2') or 0)
            y2 = float(element.getAttribute('y2') or 0)
            # Calculate midpoint of the line
            geometry['center_x'] = (x1 + x2) / 2
            geometry['center_y'] = (y1 + y2) / 2
            geometry['width'] = abs(x2 - x1)
            geometry['height'] = abs(y2 - y1)
        elif svg_type in ['polyline', 'polygon', 'path']:
            if svg_type == 'path':
                d_attr = element.getAttribute('d')
                if d_attr:
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
                    
                    if path_coords:
                        try:
                            # Extract the raw coordinate values from the path data
                            x_str = path_coords[0][0]
                            y_str = path_coords[0][1]
                            
                            # Convert to float
                            geometry['center_x'] = float(x_str)
                            geometry['center_y'] = float(y_str)
                        except (ValueError, IndexError):
                            pass
            
            # Default dimensions for these types
            if geometry['width'] == 0:
                geometry['width'] = 10
            if geometry['height'] == 0:
                geometry['height'] = 10
        
        # Apply transformations to get the actual position
        transform_matrix = self.get_all_transforms(element)
        transformed_center_x, transformed_center_y = self.apply_transform(
            (geometry['center_x'], geometry['center_y']), transform_matrix
        )
        
        geometry['center_x'] = transformed_center_x
        geometry['center_y'] = transformed_center_y
        
        return geometry
    
    def apply_group_suffix(self, element_json, group_suffix):
        """Apply a group suffix rotation to an element JSON."""
        if not element_json or not group_suffix:
            return
            
        # Get original rotation
        original_rotation = element_json['position'].get('rotate', {}).get('angle', '0deg')
        
        # Parse the original rotation
        try:
            orig_rotation_angle = float(original_rotation.replace('deg', ''))
        except (ValueError, AttributeError):
            orig_rotation_angle = 0
        
        # Calculate new rotation based on group suffix
        new_rotation = orig_rotation_angle
        if group_suffix == 'r':
            new_rotation = 0
        elif group_suffix == 'd':
            new_rotation = 90
        elif group_suffix == 'l':
            new_rotation = 180
        elif group_suffix == 'u':
            new_rotation = 270
        
        # Update the rotation in the element JSON
        if 'rotate' not in element_json['position']:
            element_json['position']['rotate'] = {'anchor': '50% 50%'}
            
        element_json['position']['rotate']['angle'] = f"{new_rotation}deg"
        
        logger.debug(f"Applied group suffix '{group_suffix}' to element {element_json['meta']['name']}, rotation: {original_rotation} → {new_rotation}deg")
        
        # Add suffix to metadata
        element_json['meta']['groupSuffix'] = group_suffix

def save_json_to_file(data, output_file):
    """Save data to a JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Elements saved to {output_file}")
        ui_print(f"Elements saved to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving elements to file: {e}")
        ui_print(f"Error saving elements to file: {e}", logging.ERROR)
        return False

def validate_with_existing(new_elements, existing_file='elements.json'):
    """Compare newly generated elements with existing ones to validate."""
    try:
        if not os.path.exists(existing_file):
            logger.info(f"No existing file {existing_file} to validate against.")
            return
            
        with open(existing_file, 'r') as f:
            existing_elements = json.load(f)
            
        if len(new_elements) != len(existing_elements):
            logger.warning(f"Warning: Element count mismatch. New: {len(new_elements)}, Existing: {len(existing_elements)}")
        
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
                    logger.warning(f"Mismatch at element {idx}:")
                    if not pos_match:
                        logger.warning(f"  Position: New ({new_el['position']['x']}, {new_el['position']['y']}) vs "
                                      f"Old ({old_el['position']['x']}, {old_el['position']['y']})")
                    if not name_match:
                        logger.warning(f"  Name: New '{new_el['meta']['name']}' vs Old '{old_el['meta']['name']}'")
                    if not element_num_match:
                        logger.warning(f"  Element Number: New {new_number} vs Old {old_number}")
                    if not tag_props_match:
                        logger.warning(f"  Tag Properties mismatch")
        
        if mismatches == 0:
            logger.info("Validation successful! All elements match.")
        else:
            logger.warning(f"Validation found {mismatches} mismatches out of {compare_length} elements.")
            
    except Exception as e:
        logger.error(f"Error during validation: {e}")
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
    parser.add_argument('-c', '--config', default='config.json', help='Path to the configuration file (default: config.json)')
    parser.add_argument('--print-only', action='store_true', help='Only print the JSON objects without saving to file')
    parser.add_argument('--validate', action='store_true', help='Validate output against existing elements.json')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        logger.info(f"Processing SVG file: {args.svg}")
        ui_print(f"Processing SVG file: {args.svg}")
        
        # Load configuration file
        config = {}
        try:
            with open(args.config, 'r') as file:
                config = json.load(file)
                if args.debug:
                    ui_print(f"Loaded configuration from {args.config}")
                    ui_print(f"Found {len(config.get('element_mappings', []))} element mappings")
        except Exception as e:
            logger.warning(f"Failed to load configuration file {args.config}: {e}")
            ui_print(f"Warning: Failed to load configuration file {args.config}: {e}", logging.WARNING)
        
        # Create transformer and process SVG
        transformer = SVGTransformer(args.svg, custom_options=config, debug=args.debug)
        elements = transformer.process_svg()
        
        # Save or print elements based on command line argument
        if args.print_only:
            logger.info("\nExtracted JSON objects:\n")
            ui_print("\nExtracted JSON objects:")
            print(json.dumps(elements, indent=2))
        else:
            save_json_to_file(elements, args.output)
        
        # Validate if requested
        if args.validate:
            validate_with_existing(elements)
        
        logger.info(f"\nSuccessfully processed {len(elements)} elements from the SVG file.")
        ui_print(f"\nSuccessfully processed {len(elements)} elements from the SVG file.")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        ui_print(f"Error: {e}", logging.ERROR)
        return 1
    
    return 0

if __name__ == "__main__":
    main() 