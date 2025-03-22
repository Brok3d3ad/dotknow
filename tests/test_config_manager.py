import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, mock_open

# Import the ConfigManager class
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from svg_processor_gui import ConfigManager, DEFAULT_CONFIG

class TestConfigManager(unittest.TestCase):
    """Unit tests for the ConfigManager class."""
    
    def setUp(self):
        """Set up a temporary directory for config file testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        
    def tearDown(self):
        """Clean up temporary files after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_init_with_existing_config(self):
        """Test initialization with an existing valid config file."""
        test_config = {
            'element_mappings': [
                {
                    'svg_type': 'rect',
                    'element_type': 'ia.display.view',
                    'props_path': 'test/path',
                    'width': 20,
                    'height': 30
                },
                {
                    'svg_type': 'circle',
                    'element_type': 'ia.custom.type',
                    'props_path': 'test/path',
                    'width': 15,
                    'height': 15
                }
            ],
            'custom_setting': 'value'
        }
        
        # Write test config to file
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Create configuration manager with the test config file
        config_manager = ConfigManager(self.config_path)
        
        # Verify that the config was loaded correctly
        loaded_config = config_manager.get_config()
        self.assertEqual(loaded_config['element_mappings'][0]['svg_type'], 'rect')
        self.assertEqual(loaded_config['element_mappings'][0]['element_type'], 'ia.display.view')
        self.assertEqual(loaded_config['element_mappings'][1]['svg_type'], 'circle')
        self.assertEqual(loaded_config['custom_setting'], 'value')
    
    def test_init_with_missing_config(self):
        """Test initialization when config file doesn't exist."""
        # Ensure the file doesn't exist
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
            
        # Create a config manager pointing to a non-existent file
        config_manager = ConfigManager(self.config_path)
        
        # Verify that the config was created with default values
        self.assertTrue(os.path.exists(self.config_path))
        loaded_config = config_manager.get_config()
        self.assertTrue('element_mappings' in loaded_config)
    
    def test_init_with_corrupted_config(self):
        """Test initialization with a corrupted config file."""
        # Create a corrupted JSON file
        with open(self.config_path, 'w') as f:
            f.write('{"this is not valid JSON')
        
        # Initialize with corrupted config file - should handle it gracefully
        config_manager = ConfigManager(self.config_path)
        
        # Verify that get_config handles the corrupted file and returns an empty dict
        loaded_config = config_manager.get_config()
        self.assertEqual(loaded_config, {})
        
        # Now fix the corrupted file with a valid save
        valid_config = {"element_mappings": []}
        result = config_manager.save_config(valid_config)
        self.assertTrue(result)
        
        # Verify the file is now valid
        with open(self.config_path, 'r') as f:
            loaded_json = json.load(f)
            self.assertTrue('element_mappings' in loaded_json)
    
    def test_save_config(self):
        """Test saving configuration to file."""
        config_manager = ConfigManager(self.config_path)
        
        # Create a test config to save
        test_config = {
            'element_type': 'test.element',
            'props_path': 'test/path',
            'element_width': '20',
            'element_height': '30'
        }
        
        # Save the config
        result = config_manager.save_config(test_config)
        
        # Verify save was successful
        self.assertTrue(result)
        
        # Verify saved config can be loaded
        with open(self.config_path, 'r') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config.get('element_type'), 'test.element')
        self.assertEqual(loaded_config.get('props_path'), 'test/path')
        self.assertEqual(loaded_config.get('element_width'), '20')
        self.assertEqual(loaded_config.get('element_height'), '30')
    
    def test_get_config(self):
        """Test retrieving the configuration."""
        # Create a test configuration
        test_config = {
            "element_mappings": [
                {
                    "svg_type": "rect",
                    "element_type": "ia.display.view",
                    "props_path": "test/path",
                    "width": 20,
                    "height": 30
                }
            ],
            "test_value": "test_setting"
        }
        
        # Write the configuration to file
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
            
        # Initialize the config manager
        config_manager = ConfigManager(self.config_path)
        
        # Get the configuration
        config = config_manager.get_config()
        
        # Verify the configuration is correct
        self.assertEqual(config["test_value"], "test_setting")
        self.assertEqual(config["element_mappings"][0]["svg_type"], "rect")
    
    def test_get_value(self):
        """Test getting a specific configuration value."""
        # Create a config manager with test config
        test_config = {
            'element_mappings': [
                {
                    'svg_type': 'rect',
                    'element_type': 'ia.display.view',
                    'props_path': 'test/path',
                    'width': 20,
                    'height': 30
                },
                {
                    'svg_type': 'circle',
                    'element_type': 'ia.custom.type',
                    'props_path': 'test/path2',
                    'width': 15,
                    'height': 15
                }
            ],
            'custom_setting': 'value',
            'nested': {
                'property': 'nested_value'
            }
        }
        
        # Write test config to file
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        config_manager = ConfigManager(self.config_path)
        loaded_config = config_manager.get_config()
        
        # Test getting values
        self.assertEqual(loaded_config['custom_setting'], 'value')
        self.assertEqual(loaded_config['nested']['property'], 'nested_value')
    
    def test_save_config_directory_error(self):
        """Test handling of directory creation error during save."""
        # Create the config manager with a temporary file
        config_manager = ConfigManager(self.config_path)
        
        # Create a directory with the same name as the config file to cause an error when saving
        os.remove(self.config_path)  # Remove the file first
        os.mkdir(self.config_path)   # Create a directory with the same name
        
        # Try to save config (should fail but gracefully handle the error)
        result = config_manager.save_config({'test_key': 'test_value'})
        
        # Verify save failed
        self.assertFalse(result)
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_config_file_error(self, mock_file):
        """Test handling of file write error during save."""
        # Set up mock to raise an error
        mock_file.side_effect = PermissionError("Permission denied")
        
        config_manager = ConfigManager(self.config_path)
        
        # Try to save config
        result = config_manager.save_config({'test_key': 'test_value'})
        
        # Verify save failed
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 