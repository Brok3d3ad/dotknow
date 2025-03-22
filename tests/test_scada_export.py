import unittest
import os
import json
import tempfile
import zipfile
from unittest.mock import patch, MagicMock, mock_open, call

# Import the necessary classes
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from svg_processor_gui import SVGProcessorApp, ConfigManager

class TestSCADAExport(unittest.TestCase):
    """Unit tests for SCADA export functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock root window
        self.root = MagicMock()
        
        # Create a mock config manager
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get_config.return_value = {
            'project_title': 'Test Project',
            'parent_project': 'Parent Project',
            'view_name': 'Test View',
            'svg_url': 'http://test.url/test.svg',
            'image_width': '800',
            'image_height': '600',
            'default_width': '1024',
            'default_height': '768'
        }
        
        # Create a temp directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.zip_file_path = os.path.join(self.temp_dir, "test_export.zip")
        
        # Create test application with mocked UI components
        self.app = self._create_mocked_app()
        
        # Mock the file dialog to return our test zip path
        patcher = patch('tkinter.filedialog.asksaveasfilename')
        self.mock_savedialog = patcher.start()
        self.mock_savedialog.return_value = self.zip_file_path
        self.addCleanup(patcher.stop)
        
        # Mock messagebox to avoid UI interactions
        patcher = patch('tkinter.messagebox.showinfo')
        self.mock_showinfo = patcher.start()
        self.addCleanup(patcher.stop)
        
        patcher = patch('tkinter.messagebox.showerror')
        self.mock_showerror = patcher.start()
        self.addCleanup(patcher.stop)
        
        # Set up test elements
        self.app.elements = [
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
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def _create_mocked_app(self):
        """Create a mocked application for testing."""
        # Initialize patches
        self.addCleanup(patch.stopall)
        
        # Patch tkinter-related functionality
        patch('tkinter.StringVar').start()
        patch('tkinter.scrolledtext.ScrolledText').start()
        patch('tkinter.ttk.Progressbar').start()
        patch('tkinter.ttk.Notebook').start()
        patch('tkinter.ttk.Style').start()
        
        # Patch set_window_icon to avoid icon loading errors in tests
        with patch.object(SVGProcessorApp, 'set_window_icon', return_value=None):
            # Create application with mocked dependencies
            app = SVGProcessorApp(
                self.root,
                config_manager=self.config_manager
            )
        
        # Mock UI components
        app.project_title = MagicMock()
        app.project_title.get.return_value = 'Test Project'
        
        app.parent_project = MagicMock()
        app.parent_project.get.return_value = 'Parent Project'
        
        app.view_name = MagicMock()
        app.view_name.get.return_value = 'Test View'
        
        app.svg_url = MagicMock()
        app.svg_url.get.return_value = 'http://test.url/test.svg'
        
        app.image_width = MagicMock()
        app.image_width.get.return_value = '800'
        
        app.image_height = MagicMock()
        app.image_height.get.return_value = '600'
        
        app.default_width = MagicMock()
        app.default_width.get.return_value = '1024'
        
        app.default_height = MagicMock()
        app.default_height.get.return_value = '768'
        
        app.status_var = MagicMock()
        
        return app
    
    @patch('tempfile.TemporaryDirectory')
    @patch('zipfile.ZipFile')
    @patch('os.walk')
    @patch('os.makedirs')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_scada_export_zip(self, mock_open, mock_json_dump, mock_makedirs, 
                                   mock_walk, mock_zipfile, mock_tempdir):
        """Test SCADA export zip creation."""
        # Setup mocks
        mock_tempdir.return_value.__enter__.return_value = self.temp_dir
        mock_walk.return_value = [
            (os.path.join(self.temp_dir, 'Test Project_2021-01-01_1200'), ['dir1'], ['project.json']),
            (os.path.join(self.temp_dir, 'Test Project_2021-01-01_1200/dir1'), [], ['view.json', 'resource.json'])
        ]
        
        # Setup zipfile mock to properly handle context manager
        mock_zipfile_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zipfile_instance
        
        # Call the export function - avoid direct assertion inside the function call
        self.app._create_scada_export_zip(self.zip_file_path, "Test Project_2021-01-01_1200")
        
        # Verify the temporary directory was created
        mock_tempdir.assert_called_once()
        
        # Verify directories were created
        self.assertTrue(mock_makedirs.called)
        
        # Check that open was called at least once
        self.assertTrue(mock_open.called, "open() was never called")
        
        # Verify zip file was created
        mock_zipfile.assert_called_once_with(self.zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    
    def test_export_scada_project_with_no_elements(self):
        """Test SCADA export with no elements to export."""
        # Clear elements
        self.app.elements = []
        
        # Call export function
        self.app.export_scada_project()
        
        # Verify error handling
        self.mock_showinfo.assert_called_once()
        self.mock_savedialog.assert_not_called()
    
    def test_export_scada_project_cancel_dialog(self):
        """Test SCADA export when user cancels the file dialog."""
        # Set up dialog to return empty path (simulating cancel)
        self.mock_savedialog.return_value = ''
        
        # Add some test elements
        self.app.elements = [{"test": "value"}]
        
        # Set up status_var for testing
        self.app.status_var = MagicMock()
        
        # Call export function
        self.app.export_scada_project()
        
        # Verify status_var was updated with cancellation message
        self.app.status_var.set.assert_any_call("Export cancelled.")
    
    @patch('PIL.Image.new')
    def test_create_thumbnail(self, mock_image_new):
        """Test thumbnail creation for SCADA project."""
        # Setup mock
        mock_image = MagicMock()
        mock_image_new.return_value = mock_image
        
        # Create a test directory
        test_view_dir = os.path.join(self.temp_dir, 'test_view')
        os.makedirs(test_view_dir, exist_ok=True)
        
        # Call the thumbnail creation method
        self.app._create_thumbnail(test_view_dir)
        
        # Verify image was created with correct parameters
        mock_image_new.assert_called_once_with('RGBA', (950, 530), (240, 240, 240, 0))
        mock_image.save.assert_called_once()
    
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_project_json(self, mock_open, mock_json_dump):
        """Test project.json file creation."""
        # Create a test directory
        test_project_dir = os.path.join(self.temp_dir, 'test_project')
        os.makedirs(test_project_dir, exist_ok=True)
        
        # Call the project.json creation method
        self.app._create_project_json(test_project_dir)
        
        # Verify file was opened correctly
        mock_open.assert_called_once_with(os.path.join(test_project_dir, 'project.json'), 'w')
        
        # Verify correct JSON was written
        call_args = mock_json_dump.call_args[0]
        self.assertEqual(call_args[0]['title'], 'Test Project')
        self.assertEqual(call_args[0]['parent'], 'Parent Project')
        self.assertEqual(call_args[0]['enabled'], True)
    
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_view_json(self, mock_open, mock_json_dump):
        """Test view.json file creation."""
        # Create a test directory
        test_view_dir = os.path.join(self.temp_dir, 'test_view')
        os.makedirs(test_view_dir, exist_ok=True)
        
        # Call the view.json creation method
        self.app._create_view_json(test_view_dir)
        
        # Verify file was opened correctly
        mock_open.assert_called_once_with(os.path.join(test_view_dir, 'view.json'), 'w')
        
        # Verify correct JSON was written
        call_args = mock_json_dump.call_args[0]
        self.assertEqual(call_args[0]['props']['defaultSize']['width'], 1024)
        self.assertEqual(call_args[0]['props']['defaultSize']['height'], 768)
        
        # Verify background image was configured
        background_image = call_args[0]['root']['children'][0]
        self.assertEqual(background_image['meta']['name'], 'Image')
        self.assertEqual(background_image['position']['width'], 800)
        self.assertEqual(background_image['position']['height'], 600)
        
        # Verify elements were added
        self.assertEqual(len(call_args[0]['root']['children']), 2)  # Background + 1 element
        
        element = call_args[0]['root']['children'][1]
        self.assertEqual(element['meta']['name'], 'TestElement1')
        self.assertEqual(element['position']['x'], 100)
        self.assertEqual(element['position']['y'], 200)

if __name__ == '__main__':
    unittest.main() 