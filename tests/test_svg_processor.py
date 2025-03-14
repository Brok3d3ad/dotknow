import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open

# Import the necessary classes
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from svg_processor_gui import SVGProcessorApp, ConfigManager

class MockSVGTransformer:
    """Mock version of SVGTransformer for testing."""
    
    def __init__(self, svg_path, options):
        self.svg_path = svg_path
        self.options = options
        
    def process_svg(self):
        """Return mock elements for testing."""
        # Return a consistent set of test elements
        return [
            {
                "meta": {
                    "name": "TestElement1"
                },
                "position": {
                    "height": 14,
                    "width": 14,
                    "x": 100,
                    "y": 200
                },
                "props": {
                    "params": {
                        "directionLeft": False,
                        "forceFaultStatus": False,
                        "forceRunningStatus": False,
                        "tagProps": ["tag1", "tag2"]
                    },
                    "path": "test/path"
                },
                "type": "ia.display.view"
            }
        ]

class TestSVGProcessor(unittest.TestCase):
    """Unit tests for SVG processing functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock root window
        self.root = MagicMock()
        
        # Create a mock config manager
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get_config.return_value = {
            'file_path': '/test/path/file.svg',
            'element_type': 'test.element',
            'props_path': 'test/path',
            'element_width': '20',
            'element_height': '30',
            'project_title': 'Test Project',
            'parent_project': 'Parent Project',
            'view_name': 'Test View',
            'svg_url': 'http://test.url/test.svg',
            'image_width': '800',
            'image_height': '600',
            'default_width': '1024',
            'default_height': '768'
        }
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_svg_path = os.path.join(self.temp_dir, "test.svg")
        
        # Create a test SVG file
        with open(self.test_svg_path, 'w') as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="100" height="100"/></svg>')
        
        # Initialize patches
        self.addCleanup(patch.stopall)
        
        # Patch tkinter-related functionality to avoid UI operations
        self.tk_mock = patch('tkinter.StringVar').start()
        self.scrolledtext_mock = patch('tkinter.scrolledtext.ScrolledText').start()
        self.progressbar_mock = patch('tkinter.ttk.Progressbar').start()
        self.notebook_mock = patch('tkinter.ttk.Notebook').start()
        self.style_mock = patch('tkinter.ttk.Style').start()
        
        # Patch set_window_icon to avoid icon loading errors in tests
        with patch.object(SVGProcessorApp, 'set_window_icon', return_value=None):
            # Create the SVGProcessorApp with mocks
            self.app = SVGProcessorApp(
                self.root,
                config_manager=self.config_manager,
                svg_transformer_class=MockSVGTransformer
            )
        
        # Patch the file operations to avoid actual file operations
        self.app.results_text = MagicMock()
        self.app.log_text = MagicMock()
        self.app.redirect = MagicMock()
        self.app.progress = MagicMock()
        self.app.process_button = MagicMock()
        self.app.notebook = MagicMock()
        self.app.file_path = MagicMock()
        self.app.file_path.get.return_value = self.test_svg_path
        
        # Mock status variable
        self.app.status_var = MagicMock()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    @patch('os.path.exists')
    def test_process_svg_with_valid_file(self, mock_exists):
        """Test processing a valid SVG file."""
        # Mock os.path.exists to return True for our test SVG file
        mock_exists.return_value = True
        
        # Mock the UI components
        self.app._get_processing_options = MagicMock(return_value={
            'type': 'test.element',
            'props_path': 'test/path',
            'width': 20,
            'height': 30
        })
        
        # Process the SVG
        self.app.process_svg()
        
        # Verify results
        self.assertEqual(len(self.app.elements), 1)
        self.assertEqual(self.app.elements[0]['meta']['name'], 'TestElement1')
        self.assertEqual(self.app.elements[0]['position']['x'], 100)
        self.assertEqual(self.app.elements[0]['position']['y'], 200)
        
        # Verify UI was updated
        self.app.results_text.delete.assert_called_once()
        self.app.log_text.delete.assert_called_once()
        self.app.status_var.set.assert_called()
        self.app.progress.start.assert_called_once()
        self.app.progress.stop.assert_called_once()
    
    @patch('os.path.exists')
    @patch('tkinter.messagebox.showerror')
    def test_process_svg_with_missing_file(self, mock_showerror, mock_exists):
        """Test processing an SVG file that doesn't exist."""
        # Mock os.path.exists to return False to simulate missing file
        mock_exists.return_value = False
        
        # Process the SVG
        self.app.process_svg()
        
        # Verify error handling
        mock_showerror.assert_called_once()
        self.assertEqual(len(self.app.elements), 0)
    
    @patch('os.path.exists')
    @patch('tkinter.messagebox.showerror')
    def test_process_svg_with_empty_path(self, mock_showerror, mock_exists):
        """Test processing with no SVG file selected."""
        # Set empty file path
        self.app.file_path.get.return_value = ''
        
        # Process the SVG
        self.app.process_svg()
        
        # Verify error handling
        mock_showerror.assert_called_once()
        self.assertEqual(len(self.app.elements), 0)
    
    def test_get_processing_options(self):
        """Test getting processing options from UI."""
        # Setup mock UI variables
        self.app.element_type = MagicMock()
        self.app.element_type.get.return_value = 'test.element'
        
        self.app.props_path = MagicMock()
        self.app.props_path.get.return_value = 'test/path'
        
        self.app.element_width = MagicMock()
        self.app.element_width.get.return_value = '20'
        
        self.app.element_height = MagicMock()
        self.app.element_height.get.return_value = '30'
        
        # Get processing options
        options = self.app._get_processing_options()
        
        # Verify options
        self.assertEqual(options['type'], 'test.element')
        self.assertEqual(options['props_path'], 'test/path')
        self.assertEqual(options['width'], 20)
        self.assertEqual(options['height'], 30)
    
    @patch('tkinter.messagebox.showinfo')
    def test_copy_to_clipboard_with_no_elements(self, mock_showinfo):
        """Test copying to clipboard when no elements are available."""
        # Set empty elements
        self.app.elements = []
        
        # Try to copy to clipboard
        self.app.copy_to_clipboard()
        
        # Verify error handling
        mock_showinfo.assert_called_once()
    
    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.messagebox.showinfo')
    def test_save_to_file_with_no_elements(self, mock_showinfo, mock_savedialog):
        """Test saving to file when no elements are available."""
        # Set empty elements
        self.app.elements = []
        
        # Try to save to file
        self.app.save_to_file()
        
        # Verify error handling
        mock_showinfo.assert_called_once()
        mock_savedialog.assert_not_called()
    
    def test_clear_results(self):
        """Test clearing results."""
        # Set some elements
        self.app.elements = [{"test": "value"}]
        
        # Clear results
        self.app.clear_results()
        
        # Verify results were cleared
        self.assertEqual(len(self.app.elements), 0)
        self.app.results_text.delete.assert_called_once()
        self.app.status_var.set.assert_called_with("Results cleared.")
    
    def test_on_closing(self):
        """Test window closing handler."""
        # Setup
        self.app._save_config_from_ui = MagicMock()
        
        # Call closing handler
        self.app.on_closing()
        
        # Verify config was saved
        self.app._save_config_from_ui.assert_called_once()
        self.root.destroy.assert_called_once()

if __name__ == '__main__':
    unittest.main() 