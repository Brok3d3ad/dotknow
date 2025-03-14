import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open, call

# Import the necessary classes
import sys
import tkinter as tk
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from svg_processor_gui import SVGProcessorApp, ConfigManager

class TestSVGProcessorUIBasics(unittest.TestCase):
    """Basic tests for the SVGProcessorApp class, focusing on high-level functionality."""
    
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
        
        # Initialize patches to avoid UI operations
        self.addCleanup(patch.stopall)
        
        # Patch all UI-related attributes to prevent GUI operations
        self.patches = [
            patch('tkinter.StringVar'),
            patch('tkinter.scrolledtext.ScrolledText'),
            patch('tkinter.ttk.Progressbar'),
            patch('tkinter.ttk.Notebook'),
            patch('tkinter.ttk.Style'),
            patch('tkinter.ttk.Frame'),
            patch('tkinter.ttk.Label'),
            patch('tkinter.ttk.Button'),
            patch('tkinter.ttk.Entry'),
            patch('tkinter.Menu'),
            patch('tkinter.Toplevel'),
            patch('tkinter.Canvas'),
            patch('tkinter.PhotoImage'),
            patch.object(SVGProcessorApp, 'set_window_icon', return_value=None)
        ]
        
        for p in self.patches:
            p.start()
            
        # Create the application with mocks
        self.app = SVGProcessorApp(
            self.root,
            config_manager=self.config_manager
        )
        
        # Mock essential UI components
        self.app.file_path = MagicMock()
        self.app.file_path.get.return_value = self.test_svg_path
        self.app.element_type = MagicMock()
        self.app.element_type.get.return_value = 'test.element'
        self.app.props_path = MagicMock()
        self.app.props_path.get.return_value = 'test/path'
        self.app.element_width = MagicMock()
        self.app.element_width.get.return_value = '20'
        self.app.element_height = MagicMock()
        self.app.element_height.get.return_value = '30'
        self.app.results_text = MagicMock()
        self.app.log_text = MagicMock()
        self.app.progress = MagicMock()
        self.app.process_button = MagicMock()
        self.app.notebook = MagicMock()
        self.app.status_var = MagicMock()
        
        # Reset elements
        self.app.elements = []
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    @patch('tkinter.filedialog.askopenfilename')
    def test_browse_file(self, mock_dialog):
        """Test file browser functionality."""
        # Set up mock dialog to return a test path
        mock_dialog.return_value = "/test/path/test.svg"
        
        # Call the method
        self.app.browse_file()
        
        # Verify dialog was called and file path was updated
        mock_dialog.assert_called_once()
        self.app.file_path.set.assert_called_with("/test/path/test.svg")
    
    @patch('tkinter.filedialog.askopenfilename')
    def test_browse_file_cancel(self, mock_dialog):
        """Test file browser when cancel is clicked."""
        # Set up mock dialog to return empty string (cancel)
        mock_dialog.return_value = ""
        
        # Call the method
        self.app.browse_file()
        
        # Verify dialog was called but file path was not updated
        mock_dialog.assert_called_once()
        self.app.file_path.set.assert_not_called()
    
    @patch('tkinter.messagebox.showinfo')
    def test_copy_to_clipboard_no_elements(self, mock_showinfo):
        """Test copying to clipboard when no elements are available."""
        # Set empty elements
        self.app.elements = []
        
        # Try to copy to clipboard
        self.app.copy_to_clipboard()
        
        # Verify error handling
        mock_showinfo.assert_called_once()
    
    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.messagebox.showinfo')
    def test_save_to_file_no_elements(self, mock_showinfo, mock_savedialog):
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
    
    @patch('os.path.exists')
    @patch('tkinter.messagebox.showerror')
    def test_process_svg_missing_file(self, mock_showerror, mock_exists):
        """Test processing an SVG file that doesn't exist."""
        # Mock os.path.exists to return False to simulate missing file
        mock_exists.return_value = False
        
        # Process the SVG
        self.app.process_svg()
        
        # Verify error handling
        mock_showerror.assert_called_once()
        
    @patch('os.path.exists')
    @patch('tkinter.messagebox.showerror')
    def test_process_svg_empty_path(self, mock_showerror, mock_exists):
        """Test processing with no SVG file selected."""
        # Set empty file path
        self.app.file_path.get.return_value = ''
        
        # Process the SVG
        self.app.process_svg()
        
        # Verify error handling
        mock_showerror.assert_called_once()
        mock_exists.assert_not_called()
    
    @patch('os.path.exists')
    def test_process_svg(self, mock_exists):
        """Test processing a valid SVG file."""
        # Mock os.path.exists to return True for our test SVG file
        mock_exists.return_value = True
        
        # Set up mocks for UI elements and processing
        self.app._get_processing_options = MagicMock(return_value={
            'type': 'test.element',
            'props_path': 'test/path',
            'width': 20,
            'height': 30
        })
        
        # Mock the SVGTransformer instance method directly
        with patch('inkscape_transform.SVGTransformer.process_svg') as mock_process_svg:
            # Mock the process_svg method to return some test elements
            mock_process_svg.return_value = [{
                "meta": {
                    "name": "TestElement1"
                },
                "position": {
                    "height": 14,
                    "width": 14,
                    "x": 100,
                    "y": 200
                },
                "type": "ia.display.view"
            }]
            
            # Process the SVG
            self.app.process_svg()
            
            # Verify process_svg was called
            mock_process_svg.assert_called_once()
            
            # Verify results were stored
            self.assertEqual(len(self.app.elements), 1)
            self.assertEqual(self.app.elements[0]['meta']['name'], 'TestElement1')
    
    @patch('tkinter.messagebox.showinfo')
    def test_export_scada_project_no_elements(self, mock_showinfo):
        """Test SCADA export with no elements to export."""
        # Clear elements
        self.app.elements = []
        
        # Call export function
        self.app.export_scada_project()
        
        # Verify error handling
        mock_showinfo.assert_called_once()
    
    @patch('tkinter.filedialog.asksaveasfilename')
    def test_export_scada_project_cancel(self, mock_savedialog):
        """Test cancellation of SCADA export."""
        # Set up mock to return empty path (cancel)
        mock_savedialog.return_value = ''
        
        # Set test elements
        self.app.elements = [{"test": "value"}]
        
        # Call export function
        with patch('tkinter.messagebox.showinfo') as mock_showinfo:
            self.app.export_scada_project()
        
        # Verify handling of cancelled dialog
        mock_showinfo.assert_called_once_with("Info", "Export cancelled.")
    
    def test_on_closing(self):
        """Test the on_closing method saves config and destroys window."""
        # Call on_closing
        self.app.on_closing()
        
        # Verify config was saved with current values
        self.config_manager.save_config.assert_called_once()
        
        # Verify window was destroyed
        self.root.destroy.assert_called_once()

if __name__ == '__main__':
    unittest.main()


class TestSVGProcessorUIIcon(unittest.TestCase):
    """Tests for the SVGProcessorApp icon functionality."""
    
    def setUp(self):
        """Set up test environment without patching the set_window_icon method."""
        # Create a mock root window
        self.root = MagicMock()
        
        # Create a mock config manager
        self.config_manager = MagicMock(spec=ConfigManager)
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch all UI-related attributes to prevent GUI operations except set_window_icon
        self.patches = [
            patch('tkinter.StringVar'),
            patch('tkinter.scrolledtext.ScrolledText'),
            patch('tkinter.ttk.Progressbar'),
            patch('tkinter.ttk.Notebook'),
            patch('tkinter.ttk.Style'),
            patch('tkinter.ttk.Frame'),
            patch('tkinter.ttk.Label'),
            patch('tkinter.ttk.Button'),
            patch('tkinter.ttk.Entry'),
            patch('tkinter.Menu'),
            patch('tkinter.Toplevel'),
            patch('tkinter.Canvas'),
            patch('tkinter.PhotoImage'),
            # Deliberately NOT patching set_window_icon
        ]
        
        for p in self.patches:
            p.start()
            
        # Create the application with mocks
        self.app = SVGProcessorApp(
            self.root,
            config_manager=self.config_manager
        )
        
        # Clean up patches on test completion
        self.addCleanup(patch.stopall)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_set_window_icon_windows(self):
        """Test setting window icon on Windows platforms."""
        # Test with .ico file on Windows
        with patch('os.path.exists', return_value=True):
            with patch('sys.platform', 'win32'):
                # Call set_window_icon
                self.app.set_window_icon()
                
                # Verify iconbitmap was called
                self.root.iconbitmap.assert_called_once()
    
    def test_set_window_icon_macos_ico(self):
        """Test setting window icon on macOS with .ico file."""
        # Test with .ico file on non-Windows (e.g., macOS)
        with patch('os.path.exists', return_value=True):
            with patch('sys.platform', 'darwin'):
                # Mock PIL.Image and ImageTk
                with patch('PIL.Image.open') as mock_image_open:
                    mock_image = MagicMock()
                    mock_image.resize.return_value = mock_image
                    mock_image_open.return_value = mock_image
                    
                    with patch('PIL.ImageTk.PhotoImage') as mock_photo:
                        # Call set_window_icon
                        self.app.set_window_icon()
                        
                        # Verify iconphoto was called (may be called multiple times)
                        self.assertTrue(self.root.iconphoto.called)
    
    def test_set_window_icon_jpg(self):
        """Test setting window icon with JPG when ICO not found."""
        # Test with JPG file when ICO not found
        with patch('os.path.exists', side_effect=lambda path: '.jpg' in path):
            with patch('sys.platform', 'darwin'):
                # Mock PIL.Image and ImageTk
                with patch('PIL.Image.open') as mock_image_open:
                    mock_image = MagicMock()
                    mock_image.resize.return_value = mock_image
                    mock_image_open.return_value = mock_image
                    
                    with patch('PIL.ImageTk.PhotoImage') as mock_photo:
                        # Call set_window_icon
                        self.app.set_window_icon()
                        
                        # Verify iconphoto was called (may be called multiple times)
                        self.assertTrue(self.root.iconphoto.called)
    
    def test_set_window_icon_error(self):
        """Test error handling when setting window icon."""
        # Test with error condition
        with patch('os.path.exists', return_value=True):
            with patch('sys.platform', 'darwin'):
                # Mock PIL.Image.open to raise an exception
                with patch('PIL.Image.open', side_effect=Exception("Test error")):
                    with patch('builtins.print') as mock_print:
                        # Call set_window_icon
                        self.app.set_window_icon()
                        
                        # Verify error was printed
                        mock_print.assert_any_call("Could not use .ico file on non-Windows platform: Test error")
    
    def test_set_window_icon_no_files(self):
        """Test behavior when no icon files are found."""
        # Test when no icon files found
        with patch('os.path.exists', return_value=False):
            with patch('builtins.print') as mock_print:
                # Call set_window_icon
                self.app.set_window_icon()
                
                # Verify no suitable icon message was printed
                mock_print.assert_called_with("No suitable icon file found for window icon") 