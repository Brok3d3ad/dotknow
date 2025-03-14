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
        # Create a test config file
        test_config = {'test_key': 'test_value'}
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Initialize ConfigManager with the test config file
        config_manager = ConfigManager(self.config_path)
        
        # Verify the config was loaded correctly
        self.assertEqual(config_manager.config.get('test_key'), 'test_value')
    
    def test_init_with_missing_config(self):
        """Test initialization when config file doesn't exist."""
        # Make sure the config file doesn't exist
        non_existent_path = os.path.join(self.temp_dir, "non_existent_config.json")
        if os.path.exists(non_existent_path):
            os.remove(non_existent_path)
        
        # Initialize ConfigManager with a non-existent config file
        config_manager = ConfigManager(non_existent_path)
        
        # Verify default config was created
        self.assertEqual(config_manager.config, DEFAULT_CONFIG)
        
        # Verify file was created
        self.assertTrue(os.path.exists(non_existent_path))
    
    def test_init_with_corrupted_config(self):
        """Test initialization with a corrupted config file."""
        # Create a corrupted JSON file
        with open(self.config_path, 'w') as f:
            f.write("{this is not valid json")
        
        # Initialize ConfigManager with the corrupted config file
        config_manager = ConfigManager(self.config_path)
        
        # Verify default config was used
        self.assertEqual(config_manager.config, DEFAULT_CONFIG)
    
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
        """Test getting a copy of the configuration."""
        # Create a test config file
        test_config = {'test_key': 'test_value'}
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Initialize ConfigManager with the test config file
        config_manager = ConfigManager(self.config_path)
        
        # Get a copy of the config
        config_copy = config_manager.get_config()
        
        # Verify the copy matches the original
        self.assertEqual(config_copy, test_config)
        
        # Modify the copy and verify the original is unchanged
        config_copy['test_key'] = 'modified_value'
        self.assertEqual(config_manager.config.get('test_key'), 'test_value')
    
    def test_get_value(self):
        """Test getting a specific configuration value."""
        # Create ConfigManager with default config
        config_manager = ConfigManager(self.config_path)
        
        # Test getting existing values
        self.assertEqual(config_manager.get_value('element_type'), 'ia.display.view')
        self.assertEqual(config_manager.get_value('props_path'), 'Symbol-Views/Equipment-Views/Status')
        
        # Test getting non-existent value with default
        self.assertEqual(config_manager.get_value('non_existent', 'default_value'), 'default_value')
        
        # Test getting non-existent value without default
        self.assertIsNone(config_manager.get_value('non_existent'))
    
    def test_save_config_directory_error(self):
        """Test handling of directory creation error during save."""
        # Create the config manager first, to avoid patching during initialization
        config_manager = ConfigManager(self.config_path)
        
        # Now patch os.makedirs specifically when save_config is called
        with patch('os.makedirs') as mock_makedirs:
            # Set up mock to raise an error
            mock_makedirs.side_effect = PermissionError("Permission denied")
            
            # Try to save config
            result = config_manager.save_config({'test_key': 'test_value'})
            
            # Verify save failed
            self.assertFalse(result)
            # Verify makedirs was called
            mock_makedirs.assert_called_once()
    
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