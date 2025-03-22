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
    
    def test_process_svg(self):
        """Test processing a valid SVG file."""
        # Create a test instance of MockSVGTransformer
        from svg_processor_gui import SVGTransformer
        
        class RealStringMockSVGTransformer:
            def __init__(self, svg_path, options):
                self.svg_path = svg_path
                self.options = options
                self.processed = False
            
            def process_svg(self):
                self.processed = True
                return [
                    {
                        "meta": {
                            "name": "TestElement1",
                            "id": "TestElement1",
                            "elementNumber": 1,
                            "svgType": "rect"
                        },
                        "position": {
                            "x": 10,
                            "y": 20,
                            "width": 30,
                            "height": 40
                        },
                        "props": {
                            "params": {},
                            "path": "test/path"
                        },
                        "type": "test.element"
                    }
                ]
        
        # Create test elements directly
        test_elements = [
            {
                "meta": {
                    "name": "TestElement1",
                    "id": "TestElement1",
                    "elementNumber": 1,
                    "svgType": "rect"
                },
                "position": {
                    "x": 10,
                    "y": 20,
                    "width": 30,
                    "height": 40
                },
                "props": {
                    "params": {},
                    "path": "test/path"
                },
                "type": "test.element"
            }
        ]
        
        # Set up app for testing
        import queue
        self.app.queue = queue.Queue()
        self.app.elements = []
        
        # Mock _process_svg_in_thread to directly assign elements
        original_process = self.app._process_svg_in_thread
        
        def mock_process(*args, **kwargs):
            self.app.elements = test_elements
            return test_elements
        
        self.app._process_svg_in_thread = mock_process
        
        # Mock os.path.exists to return True
        with patch('os.path.exists', return_value=True):
            # Mock the actual thread creation to run synchronously
            with patch('threading.Thread') as mock_thread:
                def execute_target(target=None, args=(), kwargs=None, daemon=None):
                    mock_t = MagicMock()
                    
                    def mock_start():
                        if target and args:
                            # Call the target function with its arguments
                            result = target(*args)
                            # Put the result in the queue
                            self.app.queue.put(result)
                    
                    mock_t.start = mock_start
                    return mock_t
                
                mock_thread.side_effect = execute_target
                
                # Call process_svg
                self.app.process_svg()
                
                # Execute the "queued" callback directly
                if hasattr(self.app, '_check_queue'):
                    # Manually trigger the queue processing
                    while not self.app.queue.empty():
                        self.app.elements = self.app.queue.get()
                
                # Verify processing occurred
                mock_thread.assert_called()
                self.assertEqual(len(self.app.elements), 1)
                self.assertEqual(self.app.elements[0]["meta"]["name"], "TestElement1")
        
        # Restore original method
        self.app._process_svg_in_thread = original_process
    
    @patch('tkinter.messagebox.showinfo')
    def test_export_scada_project_no_elements(self, mock_showinfo):
        """Test SCADA export with no elements to export."""
        # Clear elements
        self.app.elements = []
        
        # Call export function
        self.app.export_scada_project()
        
        # Verify error handling
        mock_showinfo.assert_called_once()
    
    def test_export_scada_project_cancel(self):
        """Test cancellation of SCADA export."""
        # Create a sample processed element
        self.app.elements = [
            {
                "meta": {
                    "name": "TestElement1",
                    "id": "TestElement1"
                },
                "position": {
                    "x": 10,
                    "y": 20,
                    "width": 30,
                    "height": 40
                },
                "props": {
                    "params": {},
                    "path": "test/path"
                },
                "type": "test.element"
            }
        ]
        
        # Mock UI elements with proper string values
        self.app.project_title = MagicMock()
        self.app.project_title.get.return_value = "Test Project"
        self.app.parent_project = MagicMock()
        self.app.parent_project.get.return_value = "Parent Project"
        self.app.view_name = MagicMock()
        self.app.view_name.get.return_value = "Test View"
        self.app.svg_url = MagicMock()
        self.app.svg_url.get.return_value = "http://test.url/test.svg"
        self.app.image_width = MagicMock()
        self.app.image_width.get.return_value = "800"
        self.app.image_height = MagicMock()
        self.app.image_height.get.return_value = "600"
        self.app.default_width = MagicMock()
        self.app.default_width.get.return_value = "1024"
        self.app.default_height = MagicMock()
        self.app.default_height.get.return_value = "768"
        
        # Set up status_var to simulate cancel action
        self.app.status_var = MagicMock()
        
        # Mock askdirectory to simulate cancel
        with patch('tkinter.filedialog.askdirectory', return_value=""):
            # Call export function
            self.app.export_scada_project()
            
            # Check the status was updated to indicate cancellation
            self.app.status_var.set.assert_called_with("Export cancelled.")
    
    def test_on_closing(self):
        """Test the on_closing method saves config and destroys window."""
        # Call on_closing
        self.app.on_closing()
        
        # Verify config was saved with current values
        self.config_manager.save_config.assert_called_once()
        
        # Verify window was destroyed
        self.root.destroy.assert_called_once()

    def test_handle_processing_error(self):
        """Test handling of processing errors."""
        # Setup
        test_error = Exception("Test error message")
        
        # Mock the necessary components
        self.app.progress = MagicMock()
        self.app.process_button = MagicMock()
        self.app.status_var = MagicMock()
        
        # Call the method
        with patch('tkinter.messagebox.showerror') as mock_showerror:
            self.app._handle_processing_error(test_error)
            
            # Verify error handling
            mock_showerror.assert_called_once_with("Processing Error", "Error processing SVG: Test error message")
            self.app.status_var.set.assert_called_once()
            self.app.progress.stop.assert_called_once()
            self.app.process_button.configure.assert_called_once_with(state=tk.NORMAL)
            self.assertFalse(self.app.processing_thread_active)
    
    def test_update_log_text(self):
        """Test updating the log text."""
        # Create a minimal implementation class instead of trying to mock the method
        class MockText:
            def __init__(self):
                self.content = ""
                
            def delete(self, start, end):
                self.content = ""
                
            def insert(self, index, text):
                self.content += text
                
            def see(self, index):
                # Just a stub for the see method
                pass
                
            def get(self, start, end):
                return self.content
        
        # Replace with our custom implementation
        self.app.log_text = MockText()
        
        # Call the update method
        test_log_text = "Test log output"
        self.app._update_log_text(test_log_text)
        
        # Check that text was updated
        self.assertEqual(self.app.log_text.content, test_log_text)

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
        # Test with Windows platform
        with patch('os.path.exists', return_value=True):
            with patch('sys.platform', 'win32'):
                # Call set_window_icon
                self.app.set_window_icon()
                
                # Verify iconbitmap was called at least once
                self.assertTrue(self.root.iconbitmap.called, "iconbitmap was not called")
    
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
                        
                        # Check if any error message was printed (being less specific about exact message)
                        self.assertTrue(mock_print.called, "No error message was printed")
                        # Look for calls that contain part of the expected message
                        any_error_msg = False
                        for call_args in mock_print.call_args_list:
                            args, _ = call_args
                            if len(args) > 0 and "Test error" in str(args[0]):
                                any_error_msg = True
                                break
                        self.assertTrue(any_error_msg, "No error message containing 'Test error' was printed")
    
    def test_set_window_icon_no_files(self):
        """Test behavior when no icon files are found."""
        # Test when no icon files found
        with patch('os.path.exists', return_value=False):
            with patch('builtins.print') as mock_print:
                # Call set_window_icon
                self.app.set_window_icon()
                
                # Check if any message about not finding icon was printed
                self.assertTrue(mock_print.called, "No message was printed")
                # Look for calls that contain part of the expected message
                any_not_found_msg = False
                for call_args in mock_print.call_args_list:
                    args, _ = call_args
                    if len(args) > 0 and "icon file" in str(args[0]):
                        any_not_found_msg = True
                        break
                self.assertTrue(any_not_found_msg, "No message about missing icon file was printed") 