import unittest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import io

# Import the SVGTransformer class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inkscape_transform import SVGTransformer, save_json_to_file, validate_with_existing, main

class TestSVGTransformer(unittest.TestCase):
    """Test the SVGTransformer class for converting SVG files."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_svg_path = os.path.join(self.temp_dir, "test.svg")
        
        # Create a test SVG file
        self.test_svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect id="rect1" x="100" y="100" width="200" height="100" />
            <rect id="rect2" x="350" y="300" width="100" height="50" transform="rotate(45)" />
        </svg>'''
        
        with open(self.test_svg_path, 'w') as f:
            f.write(self.test_svg_content)
        
        # Create test element data
        self.test_element_data = {
            'id': 'rect1',
            'x': 100,
            'y': 100,
            'width': 200,
            'height': 100,
            'center_x': 200,
            'center_y': 150,
            'transformed_x': 210,
            'transformed_y': 160
        }
        
        self.mock_svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect id="rect1" x="100" y="200" width="50" height="30" />
            <g transform="matrix(1,0,0,1,10,20)">
                <rect id="rect2" x="200" y="300" width="40" height="20" transform="rotate(120 220 310)" />
            </g>
            <g transform="scale(2)">
                <rect id="rect3" x="300" y="400" width="60" height="25" />
            </g>
            <rect id="rect4" x="150" y="250" width="45" height="35" transform="translate(5 10)" />
            <rect id="rect5" x="50" y="100" width="25" height="15" transform="matrix(1,0.5,0.5,1,10,20)" />
        </svg>'''
        
        # Use the test SVG path for initialization
        self.mock_svg_path = os.path.join(self.temp_dir, "mock.svg")
        with open(self.mock_svg_path, 'w') as f:
            f.write(self.mock_svg_content)
            
        # Now initialize with an actual path
        self.svg_transformer = SVGTransformer(self.test_svg_path)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory and test files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test SVGTransformer initialization."""
        # Test with default parameters
        transformer = SVGTransformer(self.test_svg_path)
        self.assertEqual(transformer.svg_path, self.test_svg_path)
        self.assertIsNotNone(transformer.doc)
        self.assertEqual(transformer.svg_element.tagName, 'svg')
        
        # Test with custom options
        custom_options = {'offset_x': 10, 'offset_y': 20}
        transformer = SVGTransformer(self.test_svg_path, custom_options)
        self.assertEqual(transformer.custom_options, custom_options)
    
    def test_get_svg_dimensions(self):
        """Test getting SVG dimensions."""
        width, height = self.svg_transformer.get_svg_dimensions()
        self.assertEqual(width, 800.0)
        self.assertEqual(height, 600.0)
        
        # Test with missing dimensions using a mock
        with patch('xml.dom.minidom.parse') as mock_parse:
            mock_doc = MagicMock()
            mock_svg = MagicMock()
            mock_svg.getAttribute.return_value = ''
            mock_doc.getElementsByTagName.return_value = [mock_svg]
            mock_parse.return_value = mock_doc
            
            transformer = SVGTransformer(self.test_svg_path)
            width, height = transformer.get_svg_dimensions()
            
            self.assertEqual(width, 0)
            self.assertEqual(height, 0)
    
    def test_parse_transform(self):
        """Test parsing transform attribute."""
        # Test matrix transform
        transform = "matrix(1,2,3,4,5,6)"
        matrix = self.svg_transformer.parse_transform(transform)
        expected = np.array([[1, 3, 5], [2, 4, 6], [0, 0, 1]])
        np.testing.assert_array_equal(matrix, expected)
        
        # Test translate transform
        transform = "translate(10,20)"
        matrix = self.svg_transformer.parse_transform(transform)
        expected = np.array([[1, 0, 10], [0, 1, 20], [0, 0, 1]])
        np.testing.assert_array_equal(matrix, expected)
        
        # Test scale transform
        transform = "scale(2,3)"
        matrix = self.svg_transformer.parse_transform(transform)
        expected = np.array([[2, 0, 0], [0, 3, 0], [0, 0, 1]])
        np.testing.assert_array_equal(matrix, expected)
        
        # Test rotate transform
        transform = "rotate(45)"
        matrix = self.svg_transformer.parse_transform(transform)
        angle = np.radians(45)
        expected = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1]
        ])
        np.testing.assert_array_almost_equal(matrix, expected)
    
    def test_apply_transform(self):
        """Test applying transformation matrix to a point."""
        # Create a translation matrix
        translation = np.array([[1, 0, 10], [0, 1, 20], [0, 0, 1]])
        result = self.svg_transformer.apply_transform((5, 15), translation)
        self.assertEqual(result, (15, 35))
        
        # Create a scaling matrix
        scaling = np.array([[2, 0, 0], [0, 3, 0], [0, 0, 1]])
        result = self.svg_transformer.apply_transform((5, 15), scaling)
        self.assertEqual(result, (10, 45))
    
    def test_get_all_transforms(self):
        """Test getting and combining transforms from elements and parent groups."""
        # Create a test SVGTransformer
        transformer = SVGTransformer(self.test_svg_path)
        
        # Mock a DOM element with a transform attribute
        mock_element = MagicMock()
        mock_element.getAttribute.side_effect = lambda attr: "rotate(45)" if attr == "transform" else ""
        mock_element.parentNode.nodeType = mock_element.ELEMENT_NODE
        mock_element.parentNode.tagName = "g"
        mock_element.parentNode.getAttribute.side_effect = lambda attr: "translate(10,20)" if attr == "transform" else ""
        mock_element.parentNode.parentNode.nodeType = mock_element.ELEMENT_NODE
        mock_element.parentNode.parentNode.tagName = "svg"
        mock_element.parentNode.parentNode.getAttribute.return_value = ""
        
        # Test the method
        transform = transformer.get_all_transforms(mock_element)
        
        # Verify transform is a numpy array
        self.assertIsNotNone(transform)
        self.assertIsInstance(transform, np.ndarray)
        self.assertEqual(transform.shape, (3, 3))  # Should be a 3x3 matrix
    
    def test_process_svg(self):
        """Test process_svg method."""
        result = self.svg_transformer.process_svg()
        
        # Should find 2 rectangles
        self.assertEqual(len(result), 2)
        
        # Check properties of first rectangle
        self.assertEqual(result[0]['meta']['name'], 'rect1')
        self.assertEqual(result[0]['position']['x'], 193)
        self.assertEqual(result[0]['position']['y'], 143)
    
    def test_create_element_json(self):
        """Test creating JSON representation for an element."""
        element_name = "test_element"
        rect_id = "test_id"
        rect_label = "test_label"
        rect_number = 1
        x = 100
        y = 150
        
        result = self.svg_transformer.create_element_json(element_name, rect_id, rect_label, rect_number, x, y)
        
        self.assertEqual(result['meta']['name'], element_name)
        self.assertEqual(result['position']['x'], x)
        self.assertEqual(result['position']['y'], y)

    def test_process_rectangle(self):
        """Test processing a rectangle element."""
        # Create a test SVGTransformer
        transformer = SVGTransformer(self.test_svg_path)
        
        # Mock a DOM rectangle element
        mock_rect = MagicMock()
        mock_rect.getAttribute.side_effect = lambda attr: {
            "x": "100", 
            "y": "100", 
            "width": "50", 
            "height": "50",
            "id": "test_rect",
            "transform": "",
            "inkscape:label": ""
        }.get(attr, "")
        
        # Mock the get_all_transforms method to return identity matrix
        with patch.object(transformer, 'get_all_transforms', return_value=np.identity(3)):
            # Process the rectangle
            result = transformer.process_rectangle(mock_rect, 1)
            
            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result['meta']['name'], 'rect1')
            # Position should be center - 7 pixels for offset
            self.assertEqual(result['position']['x'], 125 - 7)
            self.assertEqual(result['position']['y'], 125 - 7)

    def test_process_circle(self):
        """Test processing a circle element."""
        # This test will be implemented later when the circle processing is implemented
        pass
    
    def test_process_ellipse(self):
        """Test processing an ellipse element."""
        # This test will be implemented later when the ellipse processing is implemented
        pass
    
    def test_process_line(self):
        """Test processing a line element."""
        # This test will be implemented later when the line processing is implemented
        pass
    
    def test_process_polyline(self):
        """Test processing a polyline element."""
        # This test will be implemented later when the polyline processing is implemented
        pass
    
    def test_process_polygon(self):
        """Test processing a polygon element."""
        # This test will be implemented later when the polygon processing is implemented
        pass
    
    def test_process_path(self):
        """Test processing a path element."""
        # This test will be implemented later when the path processing is implemented
        pass
    
    def test_process_text(self):
        """Test processing a text element."""
        # This test will be implemented later when the text processing is implemented
        pass

    def test_svg_file_not_found(self):
        """Test error handling when SVG file is not found."""
        with patch('xml.dom.minidom.parse', side_effect=FileNotFoundError()):
            with self.assertRaises(FileNotFoundError):
                SVGTransformer("nonexistent.svg")

    def test_invalid_svg(self):
        """Test error handling with invalid SVG content."""
        invalid_svg = "This is not valid SVG content"
        invalid_svg_path = os.path.join(self.temp_dir, "invalid.svg")
        with open(invalid_svg_path, 'w') as f:
            f.write(invalid_svg)
            
        with self.assertRaises(Exception):
            SVGTransformer(invalid_svg_path)

class TestStandaloneFunctions(unittest.TestCase):
    """Test the standalone functions in the inkscape_transform module."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_file = os.path.join(self.temp_dir, "test_output.json")
        
        # Create sample test data with proper structure to match validate_with_existing requirements
        self.test_data = [
            {
                "type": "ia.display.view",
                "meta": {"name": "test1", "originalName": "rect1", "rectNumber": 1},
                "position": {"x": 100, "y": 150, "width": 14, "height": 14},
                "props": {
                    "params": {
                        "tagProps": ["test1", "value", "value", "value", "value", "value", "value", "value", "value", "value"]
                    }
                }
            },
            {
                "type": "ia.display.view",
                "meta": {"name": "test2", "originalName": "rect2", "rectNumber": 2},
                "position": {"x": 200, "y": 250, "width": 14, "height": 14},
                "props": {
                    "params": {
                        "tagProps": ["test2", "value", "value", "value", "value", "value", "value", "value", "value", "value"]
                    }
                }
            }
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_json_to_file(self):
        """Test saving JSON data to a file."""
        # Test successful save
        with patch('builtins.print') as mock_print:
            result = save_json_to_file(self.test_data, self.test_output_file)
            self.assertTrue(result)
            mock_print.assert_called_with(f"Elements saved to {self.test_output_file}")
        
        # Verify file was created with correct content
        self.assertTrue(os.path.exists(self.test_output_file))
        with open(self.test_output_file, 'r') as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data, self.test_data)
        
        # Test error handling
        with patch('builtins.open', side_effect=IOError("Test IO error")):
            with patch('builtins.print') as mock_print:
                result = save_json_to_file(self.test_data, "/invalid/path/test.json")
                self.assertFalse(result)
                mock_print.assert_called_with("Error saving elements to file: Test IO error")
    
    def test_validate_with_existing(self):
        """Test validation against existing file."""
        # Create an existing file
        existing_data = self.test_data.copy()
        existing_file = os.path.join(self.temp_dir, "existing.json")
        with open(existing_file, 'w') as f:
            json.dump(existing_data, f)
        
        # Test validation with matching data
        with patch('builtins.print') as mock_print:
            validate_with_existing(self.test_data, existing_file)
            mock_print.assert_called_with("Validation successful! All elements match.")
        
        # Test validation with different data
        modified_data = self.test_data.copy()
        modified_data[0]["position"]["x"] = 101  # Change one value
        
        with patch('builtins.print') as mock_print:
            validate_with_existing(modified_data, existing_file)
            mock_print.assert_any_call("Validation found 1 mismatches out of 2 elements.")
        
        # Test validation with non-existent file
        with patch('builtins.print') as mock_print:
            validate_with_existing(self.test_data, "nonexistent.json")
            mock_print.assert_called_with("No existing file nonexistent.json to validate against.")
        
        # Test validation with error
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=Exception("Test error")):
                with patch('builtins.print') as mock_print:
                    validate_with_existing(self.test_data, existing_file)
                    mock_print.assert_any_call("Error during validation: Test error")
    
    def test_main_function(self):
        """Test the main function."""
        # Test successful processing
        test_args = [
            "inkscape_transform.py",
            "--svg", self.temp_dir + "/test.svg",
            "--output", self.test_output_file
        ]
        
        # Create a test SVG file
        test_svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect id="rect1" x="100" y="100" width="200" height="100" />
        </svg>'''
        test_svg_path = os.path.join(self.temp_dir, "test.svg")
        with open(test_svg_path, 'w') as f:
            f.write(test_svg_content)
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                result = main()
                self.assertEqual(result, 0)
                mock_print.assert_any_call(f"Processing SVG file: {test_svg_path}")
        
        # Test print-only mode
        test_args = [
            "inkscape_transform.py",
            "--svg", test_svg_path,
            "--print-only"
        ]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                with patch('json.dumps', return_value="[test json output]") as mock_dumps:
                    result = main()
                    self.assertEqual(result, 0)
                    mock_print.assert_any_call("\nExtracted JSON objects:\n")
                    mock_print.assert_any_call("[test json output]")
        
        # Test validation mode
        test_args = [
            "inkscape_transform.py",
            "--svg", test_svg_path,
            "--output", self.test_output_file,
            "--validate"
        ]
        
        with patch('sys.argv', test_args):
            with patch('inkscape_transform.validate_with_existing') as mock_validate:
                result = main()
                self.assertEqual(result, 0)
                mock_validate.assert_called_once()
        
        # Test error handling
        test_args = [
            "inkscape_transform.py",
            "--svg", "nonexistent.svg"
        ]
        
        with patch('sys.argv', test_args):
            with patch('builtins.print') as mock_print:
                result = main()
                self.assertEqual(result, 1)
                mock_print.assert_any_call(f"Processing SVG file: nonexistent.svg")

if __name__ == '__main__':
    unittest.main() 