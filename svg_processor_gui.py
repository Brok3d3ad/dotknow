"""
SVG Processor GUI - A tool for processing SVG files for automation systems.

This application provides a graphical user interface for processing SVG files
and converting them to a custom JSON format for use in automation systems.
It allows users to:

1. Browse and select SVG files
2. Configure processing options
3. Process SVG files to extract elements
4. Copy the results to clipboard or save to a file
5. Export to Ignition SCADA project structure as a zip file

The application uses the SVGTransformer class from inkscape_transform.py
to handle the actual SVG processing.

Author: Automation Standards Team
License: Proprietary
"""

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import json
import os
import sys
import io
import zipfile
import tempfile
from datetime import datetime
from contextlib import redirect_stdout
from inkscape_transform import SVGTransformer
from PIL import Image, ImageTk  # For handling images
import re
import threading
import queue

# Config file path - with PyInstaller compatibility
def get_application_path():
    """Get the base path for the application, works for both dev and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (PyInstaller)
        # Use the directory of the executable
        return os.path.dirname(sys.executable)
    else:
        # If running as a regular Python script
        return os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    This function helps locate resources whether running from source or
    from a packaged executable.
    
    Args:
        relative_path (str): Path relative to the script or executable
        
    Returns:
        str: Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path is None:
            # Fall back to application directory
            base_path = get_application_path()
    except Exception:
        base_path = get_application_path()
    
    return os.path.join(base_path, relative_path)

# Default configuration values
DEFAULT_CONFIG = {
    'file_path': '',
    'element_type': 'ia.display.view',
    'props_path': 'Symbol-Views/Equipment-Views/Status',
    'element_width': '14',
    'element_height': '14',
    'project_title': 'MTN6_SCADA',
    'parent_project': 'SCADA_PERSPECTIVE_PARENT_PROJECT',
    'view_name': 'Bulk Inbound Problem Solve',
    'svg_url': 'http://127.0.0.1:5500/bulk_inbound_problemsolve.svg',
    'image_width': '1920',
    'image_height': '1080',
    'default_width': '1920',
    'default_height': '1080'
}

class ConfigManager:
    """
    Handles loading, saving, and accessing application configuration.
    
    This class provides methods to manage the application's configuration,
    including loading from file, saving to file, and accessing configuration values.
    It also handles creating default configuration when necessary.
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str, optional): Path to the configuration file.
                If None, uses the default location in the application directory.
        """
        self.config_dir = get_application_path()
        self.config_file = config_file or os.path.join(self.config_dir, "app_config.json")
        self.config = self._load_or_create_config()
        
    def _load_or_create_config(self):
        """
        Load existing config or create default if none exists.
        
        Returns:
            dict: The loaded or created configuration dictionary.
        """
        # Ensure config directory exists
        try:
            os.makedirs(self.config_dir, exist_ok=True)
        except (PermissionError, OSError):
            return DEFAULT_CONFIG.copy()
        
        if not os.path.exists(self.config_file):
            return self._create_default_config()
        
        try:
            with open(self.config_file, 'r') as config_file:
                config = json.load(config_file)
                # Validate the loaded config and add any missing keys
                return self._validate_and_update_config(config)
        except (json.JSONDecodeError, PermissionError, Exception):
            return DEFAULT_CONFIG.copy()
    
    def _validate_and_update_config(self, config):
        """
        Validate loaded configuration and add any missing default values.
        
        Args:
            config (dict): The loaded configuration dictionary.
        
        Returns:
            dict: The validated and updated configuration dictionary.
        """
        validated_config = DEFAULT_CONFIG.copy()
        
        # Update with values from loaded config
        for key, default_value in DEFAULT_CONFIG.items():
            if key in config:
                validated_config[key] = config[key]
        
        return validated_config
    
    def _create_default_config(self):
        """
        Create and save default configuration.
        
        Returns:
            dict: The default configuration dictionary.
        """
        try:
            with open(self.config_file, 'w') as config_file:
                json.dump(DEFAULT_CONFIG, config_file, indent=4)
            return DEFAULT_CONFIG.copy()
        except Exception:
            return DEFAULT_CONFIG.copy()
    
    def save_config(self, updated_config):
        """
        Save the current configuration to file.
        
        Args:
            updated_config (dict): The configuration dictionary to save.
        
        Returns:
            bool: True if the configuration was saved successfully, False otherwise.
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Validate the configuration before saving
            validated_config = self._validate_and_update_config(updated_config)
            
            with open(self.config_file, 'w') as config_file:
                json.dump(validated_config, config_file, indent=4)
            self.config = validated_config
            return True
        except Exception:
            return False
    
    def get_config(self):
        """
        Get a copy of the current configuration.
        
        Returns:
            dict: A copy of the current configuration dictionary.
        """
        return self.config.copy()
    
    def get_value(self, key, default=None):
        """
        Get a specific configuration value.
        
        Args:
            key (str): The configuration key to get.
            default: The default value to return if the key doesn't exist.
        
        Returns:
            The value for the specified key, or the default value if the key doesn't exist.
        """
        return self.config.get(key, default)
    
    def set_value(self, key, value):
        """
        Set a specific configuration value and save the configuration.
        
        Args:
            key (str): The configuration key to set.
            value: The value to set for the key.
            
        Returns:
            bool: True if the value was set and saved successfully, False otherwise.
        """
        updated_config = self.get_config()
        updated_config[key] = value
        return self.save_config(updated_config)

class RedirectText:
    """
    Redirect stdout to a tkinter widget.
    
    This class provides a file-like interface to redirect standard output
    to a tkinter text widget. It's used to capture console output for
    display in the GUI.
    """
    def __init__(self, text_widget):
        """
        Initialize the stdout redirector.
        
        Args:
            text_widget: A tkinter text or scrolledtext widget to receive the output.
        """
        self.text_widget = text_widget
        self.buffer = io.StringIO()
        self.text_buffer = ""
        
    def write(self, string):
        """
        Write string to the buffer and text widget.
        
        This method is called when text is written to stdout.
        
        Args:
            string (str): The string to write to the widget.
        """
        try:
            # Write to buffer
            self.buffer.write(string)
            
            # Accumulate text and schedule updates in batches for smoother UI
            self.text_buffer += string
            if len(self.text_buffer) >= 100 or '\n' in self.text_buffer:
                self._flush_text_buffer()
        except Exception as e:
            # Handle other errors
            print(f"Unexpected error writing to text widget: {e}")
    
    def _flush_text_buffer(self):
        """Flush accumulated text to the widget for smoother UI updates."""
        if not self.text_buffer:
            return
            
        try:
            # Add the text to the widget
            self.text_widget.insert(tk.END, self.text_buffer)
            self.text_widget.see(tk.END)  # Auto-scroll to the end
            
            # Only call update_idletasks occasionally to reduce UI freezing
            if '\n' in self.text_buffer:
                self.text_widget.update_idletasks()
                
            # Clear the buffer
            self.text_buffer = ""
        except tk.TclError as e:
            # Handle tkinter errors (e.g., widget destroyed)
            print(f"Error writing to text widget: {e}")
            self.text_buffer = ""
    
    def flush(self):
        """
        Flush the buffer.
        
        This method is called when the buffer needs to be flushed.
        It's required for file-like objects.
        """
        try:
            self.buffer.flush()
            self._flush_text_buffer()
        except Exception as e:
            print(f"Error flushing buffer: {e}")
    
    def getvalue(self):
        """
        Get the current value of the buffer.
        
        Returns:
            str: The current value of the buffer.
        """
        return self.buffer.getvalue()

class SVGProcessorApp:
    """
    Main application class for the SVG Processor.
    
    This class handles the user interface and coordinates the various
    components of the application.
    """
    
    def __init__(self, root, config_manager=None, svg_transformer_class=SVGTransformer):
        """
        Initialize the application.
        
        Args:
            root: The Tkinter root window.
            config_manager: An optional ConfigManager instance for configuration handling.
            svg_transformer_class: The SVGTransformer class to use for processing SVGs.
        """
        self.root = root
        self.root.title("SVG Processor")
        self.root.minsize(800, 600)
        self.root.geometry("1000x700")
        
        # Dependency injection for easier testing
        self.config_manager = config_manager or ConfigManager()
        self.svg_transformer_class = svg_transformer_class
        
        # Store the processed elements
        self.elements = []
        
        # Create a queue for thread communication
        self.queue = queue.Queue()
        
        # Thread status flag
        self.processing_thread_active = False
        
        # Initialize the application UI
        self._init_application()
        
        # Set up queue checking for thread results
        self._setup_queue_check()
    
    def _init_application(self):
        """Initialize the application components."""
        # Configure the theme
        self.configure_theme()
        
        # Set window icon
        self.set_window_icon()
        
        # Initialize UI components
        self._init_ui_variables()
        
        # Create UI sections
        self._create_ui_sections()
        
        # Load saved configuration
        self._load_config_to_ui()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_ui_sections(self):
        """Create all UI sections."""
        self._create_form_frame()
        self._create_scada_frame()
        self._create_button_frame()
        self._create_notebook()
        self._create_status_bar()
    
    def _init_ui_variables(self):
        """Initialize UI variables."""
        self.file_path = tk.StringVar()
        self.element_type = tk.StringVar(value=DEFAULT_CONFIG["element_type"])
        self.props_path = tk.StringVar(value=DEFAULT_CONFIG["props_path"])
        self.element_width = tk.StringVar(value=DEFAULT_CONFIG["element_width"])
        self.element_height = tk.StringVar(value=DEFAULT_CONFIG["element_height"])
        self.project_title = tk.StringVar(value=DEFAULT_CONFIG["project_title"])
        self.parent_project = tk.StringVar(value=DEFAULT_CONFIG["parent_project"])
        self.view_name = tk.StringVar(value=DEFAULT_CONFIG["view_name"])
        self.svg_url = tk.StringVar(value=DEFAULT_CONFIG["svg_url"])
        self.image_width = tk.StringVar(value=DEFAULT_CONFIG["image_width"])
        self.image_height = tk.StringVar(value=DEFAULT_CONFIG["image_height"])
        self.default_width = tk.StringVar(value=DEFAULT_CONFIG["default_width"])
        self.default_height = tk.StringVar(value=DEFAULT_CONFIG["default_height"])
        self.status_var = tk.StringVar(value="Ready")
    
    def _create_form_frame(self):
        """Create the main form frame with input fields."""
        form_frame = ttk.Frame(self.root, padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # File selection
        ttk.Label(form_frame, text="SVG File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        ttk.Button(form_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Element type field
        ttk.Label(form_frame, text="Element Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.element_type).grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Props path field
        ttk.Label(form_frame, text="Properties Path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.props_path).grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Element sizing fields
        sizing_frame = ttk.Frame(form_frame)
        sizing_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(form_frame, text="Element Size:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Label(sizing_frame, text="Width:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(sizing_frame, textvariable=self.element_width, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(sizing_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(sizing_frame, textvariable=self.element_height, width=5).pack(side=tk.LEFT, padx=5)
        
        # Configure grid column weights
        form_frame.columnconfigure(1, weight=1)
    
    def _create_scada_frame(self):
        """Create the SCADA project settings frame."""
        scada_frame = ttk.LabelFrame(self.root, text="Ignition SCADA Project Settings", padding=10)
        scada_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Project Title
        ttk.Label(scada_frame, text="Project Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(scada_frame, textvariable=self.project_title).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Parent Project
        ttk.Label(scada_frame, text="Parent Project:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(scada_frame, textvariable=self.parent_project).grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # View Name
        ttk.Label(scada_frame, text="View Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(scada_frame, textvariable=self.view_name).grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # SVG Image URL
        ttk.Label(scada_frame, text="SVG URL:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(scada_frame, textvariable=self.svg_url).grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Image dimensions frame
        image_dim_frame = ttk.Frame(scada_frame)
        image_dim_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Image width and height
        ttk.Label(scada_frame, text="Image Dimensions:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Label(image_dim_frame, text="Width:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(image_dim_frame, textvariable=self.image_width, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(image_dim_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(image_dim_frame, textvariable=self.image_height, width=6).pack(side=tk.LEFT, padx=5)
        
        # Default Size dimensions frame
        default_dim_frame = ttk.Frame(scada_frame)
        default_dim_frame.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Default Size width and height
        ttk.Label(scada_frame, text="Default Size:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Label(default_dim_frame, text="Width:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(default_dim_frame, textvariable=self.default_width, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(default_dim_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(default_dim_frame, textvariable=self.default_height, width=6).pack(side=tk.LEFT, padx=5)
        
        # Configure grid column weights
        scada_frame.columnconfigure(1, weight=1)
    
    def _create_button_frame(self):
        """Create the button frame with action buttons."""
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill=tk.X, padx=10)
        
        # Process button
        self.process_button = ttk.Button(button_frame, text="Process SVG", command=self.process_svg)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        # Copy to clipboard button
        self.copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        # Save to file button
        self.save_button = ttk.Button(button_frame, text="Save to File", command=self.save_to_file)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Clear results button
        self.clear_button = ttk.Button(button_frame, text="Clear Results", command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Export to SCADA button
        self.export_scada_button = ttk.Button(button_frame, text="Export SCADA Project", command=self.export_scada_project)
        self.export_scada_button.pack(side=tk.LEFT, padx=5)
    
    def _create_notebook(self):
        """Create the notebook with results and log tabs."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results tab
        results_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(results_frame, text="Results")
        
        # Results text area with scrollbar
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, bg='#111111', fg='#FFDD00')
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Log tab
        log_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_frame, text="Processing Log")
        
        # Log text area with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg='#111111', fg='#FFDD00')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Redirect stdout to the log text widget
        self.redirect = RedirectText(self.log_text)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def configure_theme(self):
        """Configure the black and yellow theme."""
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure colors
        style.configure('TFrame', background='#222222')
        style.configure('TLabel', background='#222222', foreground='#FFDD00')
        style.configure('TButton', background='#333333', foreground='#FFDD00')
        style.configure('TEntry', fieldbackground='#111111', foreground='#FFDD00', insertcolor='#FFDD00')
        style.configure('TLabelframe', background='#222222', foreground='#FFDD00')
        style.configure('TLabelframe.Label', background='#222222', foreground='#FFDD00')
        style.configure('TNotebook', background='#222222', tabmargins=[2, 5, 2, 0])
        style.configure('TNotebook.Tab', background='#333333', foreground='#FFDD00', padding=[5, 2])
        style.map('TNotebook.Tab', background=[('selected', '#111111')], foreground=[('selected', '#FFDD00')])
        style.configure('TProgressbar', background='#FFDD00', troughcolor='#333333')
        
        # Set the main window background
        self.root.configure(background='#222222')
    
    def set_window_icon(self):
        """
        Set the window icon to the autStand logo.
        
        This method tries to locate and set the application icon
        from different possible locations, with fallbacks.
        """
        try:
            # Get platform info for platform-specific handling
            is_windows = sys.platform.startswith('win')
            
            # Try to find icon files using resource_path
            icon_path = self._find_icon_file()
            if not icon_path:
                print("Could not find icon file.")
                return
                
            # Apply the icon based on platform
            if icon_path.endswith('.ico'):
                self._apply_ico_icon(icon_path, is_windows)
            elif icon_path.endswith('.jpg') or icon_path.endswith('.png'):
                self._apply_image_icon(icon_path)
                
        except Exception as e:
            print(f"Error setting window icon: {e}")
    
    def _find_icon_file(self):
        """
        Find the icon file using resource_path to ensure it works in both
        development and PyInstaller environments.
        
        Returns:
            str: The path to the icon file, or None if not found.
        """
        # Try icon files in order of preference
        icon_files = [
            "autStand_ic0n.ico",
            "autstand_icon.ico",
            "automation_standard_logo.jpg"
        ]
        
        # Check each file
        for icon_file in icon_files:
            try:
                path = resource_path(icon_file)
                if os.path.exists(path):
                    return path
            except Exception:
                continue
                
        return None
    
    def _apply_ico_icon(self, icon_path, is_windows):
        """
        Apply an .ico file as the window icon.
        
        Args:
            icon_path (str): The path to the .ico file.
            is_windows (bool): Whether the platform is Windows.
        """
        print(f"Applying .ico icon from: {icon_path}")
        if is_windows:
            try:
                # Windows can use iconbitmap directly
                self.root.iconbitmap(icon_path)
                print("Applied icon using iconbitmap")
                
                # Also try to create a PhotoImage for the taskbar/tray icon
                self._apply_photo_image_from_icon(icon_path)
            except Exception as e:
                print(f"Error applying iconbitmap: {e}")
                # Fall back to photo image if iconbitmap fails
                self._apply_photo_image_from_icon(icon_path)
        else:
            # For non-Windows, convert .ico to PhotoImage
            self._apply_photo_image_from_icon(icon_path)
    
    def _apply_photo_image_from_icon(self, icon_path):
        """
        Create and apply a PhotoImage from an icon file.
        
        Args:
            icon_path (str): The path to the icon file.
        """
        try:
            print(f"Creating PhotoImage from: {icon_path}")
            icon_img = Image.open(icon_path)
            
            # Set the default icon
            default_photo = ImageTk.PhotoImage(icon_img.resize((32, 32), Image.LANCZOS))
            self.root.iconphoto(True, default_photo)
            print("Applied icon using iconphoto")
            
            # Force the window to refresh its taskbar icon
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error creating PhotoImage from icon: {e}")
    
    def _apply_image_icon(self, image_path):
        """
        Apply an image file (.jpg, .png) as the window icon.
        
        Args:
            image_path (str): The path to the image file.
        """
        try:
            print(f"Creating image icon from: {image_path}")
            # Convert image to PhotoImage for icon
            icon_img = Image.open(image_path)
            # Resize to standard icon size
            icon_img = icon_img.resize((32, 32), Image.LANCZOS)
            icon_photo = ImageTk.PhotoImage(icon_img)
            
            # Set as icon
            self.root.iconphoto(True, icon_photo)
            print("Applied image as icon using iconphoto")
        except Exception as e:
            print(f"Error applying image as icon: {e}")
            
        # Force the window to refresh its icon
        self.root.update_idletasks()
    
    def _load_config_to_ui(self):
        """
        Load configuration values into UI elements.
        
        This method loads saved configuration values from the config manager
        and updates the UI elements accordingly.
        """
        try:
            config = self.config_manager.get_config()
            
            # Map configuration keys to UI variables
            config_to_ui_map = {
                'file_path': self.file_path,
                'element_type': self.element_type,
                'props_path': self.props_path,
                'element_width': self.element_width,
                'element_height': self.element_height,
                'project_title': self.project_title,
                'parent_project': self.parent_project,
                'view_name': self.view_name,
                'svg_url': self.svg_url,
                'image_width': self.image_width,
                'image_height': self.image_height,
                'default_width': self.default_width,
                'default_height': self.default_height
            }
            
            # Update form fields with saved values
            for config_key, ui_var in config_to_ui_map.items():
                if config_key in config and config[config_key]:
                    ui_var.set(config[config_key])
        except Exception:
            # Fall back to default values if loading fails
            pass
    
    def _save_config_from_ui(self):
        """
        Save current UI values to configuration.
        
        This method collects values from UI elements and saves them
        to the configuration manager.
        
        Returns:
            bool: True if the configuration was saved successfully, False otherwise.
        """
        try:
            updated_config = {
                'file_path': self.file_path.get(),
                'element_type': self.element_type.get(),
                'props_path': self.props_path.get(),
                'element_width': self.element_width.get(),
                'element_height': self.element_height.get(),
                'project_title': self.project_title.get(),
                'parent_project': self.parent_project.get(),
                'view_name': self.view_name.get(),
                'svg_url': self.svg_url.get(),
                'image_width': self.image_width.get(),
                'image_height': self.image_height.get(),
                'default_width': self.default_width.get(),
                'default_height': self.default_height.get()
            }
            
            return self.config_manager.save_config(updated_config)
        except Exception:
            return False
    
    def browse_file(self):
        """
        Open a file dialog to select an SVG file.
        
        This method opens a file dialog for the user to select an SVG file,
        updates the file path in the UI, and updates the status bar.
        """
        try:
            # Determine initial directory from current file path if available
            initial_dir = None
            if self.file_path.get():
                initial_dir = os.path.dirname(self.file_path.get())
                
            filetypes = [
                ("SVG files", "*.svg"),
                ("All files", "*.*")
            ]
            
            filename = filedialog.askopenfilename(
                title="Select SVG File",
                filetypes=filetypes,
                initialdir=initial_dir
            )
            
            if filename:
                self.file_path.set(filename)
                self.status_var.set(f"Selected file: {os.path.basename(filename)}")
                
                # Update SVG URL if it's empty or has a default value
                current_url = self.svg_url.get()
                if not current_url or current_url == DEFAULT_CONFIG["svg_url"]:
                    # Create a basic URL from the filename
                    file_basename = os.path.basename(filename)
                    self.svg_url.set(f"http://127.0.0.1:5500/{file_basename}")
                
                # Save the configuration to preserve the file path
                self._save_config_from_ui()
                
        except Exception as e:
            self.status_var.set("Error selecting file")
            print(f"Error in file selection: {e}")
    
    def _setup_queue_check(self):
        """Set up periodic queue checking for thread results."""
        # Schedule the first check
        self.root.after(100, self._check_queue)
    
    def _check_queue(self):
        """Check for results from background processing thread."""
        try:
            # Non-blocking check
            if not self.queue.empty():
                result = self.queue.get_nowait()
                
                # Check if result is an error
                if isinstance(result, Exception):
                    self._handle_processing_error(result)
                else:
                    # Handle successful result
                    self.elements = result
                    self._display_results(result)
                    self.status_var.set(f"Processed {len(result)} elements successfully.")
                
                # Clean up processing state
                self.processing_thread_active = False
                self.progress.stop()
                self.process_button.configure(state=tk.NORMAL)
                
                # Save the configuration
                self._save_config_from_ui()
                
                # Switch back to the results tab after a short delay
                self.root.after(500, lambda: self.notebook.select(0))
        except queue.Empty:
            # Queue is empty, do nothing
            pass
        except Exception as e:
            print(f"Error checking thread queue: {e}")
        
        # Schedule the next check
        self.root.after(100, self._check_queue)
    
    def _handle_processing_error(self, error):
        """Handle an error result from the processing thread."""
        self.status_var.set(f"Processing failed: {str(error)}")
        messagebox.showerror("Processing Error", f"Error processing SVG: {str(error)}")
        self.progress.stop()
        self.process_button.configure(state=tk.NORMAL)
        self.processing_thread_active = False
    
    def _process_svg_in_thread(self, svg_path, custom_options):
        """Process the SVG file in a background thread."""
        try:
            # Create a StringIO to capture stdout
            log_output = io.StringIO()
            with redirect_stdout(log_output):
                transformer = self.svg_transformer_class(svg_path, custom_options)
                elements = transformer.process_svg()
            
            # Update the log text from the main thread
            log_text = log_output.getvalue()
            self.root.after(0, lambda: self._update_log_text(log_text))
            
            # Put the result in the queue for the main thread to process
            self.queue.put(elements)
        except Exception as e:
            # Put the exception in the queue for the main thread to handle
            self.queue.put(e)
    
    def _update_log_text(self, text):
        """Update the log text widget with captured output."""
        if text:
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
    
    def process_svg(self):
        """Process the selected SVG file and display results."""
        svg_path = self.file_path.get()
        
        if not svg_path:
            messagebox.showerror("Error", "Please select an SVG file first.")
            return
        
        if not os.path.exists(svg_path):
            messagebox.showerror("Error", f"File not found: {svg_path}")
            return
        
        # Prevent multiple processing threads
        if self.processing_thread_active:
            messagebox.showinfo("Processing", "SVG processing is already in progress.")
            return
            
        try:
            # Clear previous results
            self.results_text.delete(1.0, tk.END)
            self.log_text.delete(1.0, tk.END)
            
            # Update UI to show processing state
            self.status_var.set("Processing...")
            self.progress.start()
            self.process_button.configure(state=tk.DISABLED)
            self.root.update_idletasks()  # Update UI to show status change
            
            # Get custom options from form
            try:
                custom_options = self._get_processing_options()
            except ValueError as e:
                messagebox.showerror("Input Error", f"Invalid input values: {str(e)}")
                self.status_var.set("Processing failed: Invalid input values")
                self.progress.stop()
                self.process_button.configure(state=tk.NORMAL)
                return
            
            # Start a background thread for SVG processing
            self.processing_thread_active = True
            processing_thread = threading.Thread(
                target=self._process_svg_in_thread,
                args=(svg_path, custom_options),
                daemon=True  # Thread will exit when main program exits
            )
            processing_thread.start()
            
            # Switch to log tab to show processing progress
            self.notebook.select(1)  # Index 1 is the log tab
            
        except Exception as e:
            self.status_var.set("Error processing file.")
            messagebox.showerror("Processing Error", f"Error: {str(e)}")
            
            # Log the detailed error
            import traceback
            traceback_str = traceback.format_exc()
            print(f"Error details:\n{traceback_str}")
            
            # Always ensure UI is updated properly
            self.progress.stop()
            self.process_button.configure(state=tk.NORMAL)
            self.processing_thread_active = False
    
    def _get_processing_options(self):
        """
        Get processing options from the UI.
        
        Returns:
            dict: The processing options.
            
        Raises:
            ValueError: If any input values are invalid.
        """
        try:
            # Validate width and height are positive integers
            width = int(self.element_width.get())
            height = int(self.element_height.get())
            
            if width <= 0 or height <= 0:
                raise ValueError("Element width and height must be positive integers")
            
            element_type = self.element_type.get()
            props_path = self.props_path.get()
            
            if not element_type or not props_path:
                raise ValueError("Element type and properties path cannot be empty")
                
            return {
                'type': element_type,
                'props_path': props_path,
                'width': width,
                'height': height
            }
        except ValueError as e:
            if "invalid literal for int" in str(e):
                raise ValueError("Element width and height must be valid integers")
            else:
                raise
    
    def _display_results(self, elements):
        """
        Display the processing results in the UI.
        
        Args:
            elements (list): The processed SVG elements.
        """
        if not elements:
            self.results_text.insert(tk.END, "No elements found in the SVG file.")
            self.status_var.set("Processed SVG but found no elements.")
            return
            
        try:
            # Format results with indentation for better readability
            formatted_json = json.dumps(elements, indent=2)
            
            # For large results, insert in chunks to prevent UI freezing
            if len(formatted_json) > 50000:  # Large result threshold
                self.status_var.set(f"Processing large result ({len(formatted_json)} chars)...")
                self._insert_large_text(self.results_text, formatted_json)
            else:
                self.results_text.insert(tk.END, formatted_json)
            
            num_elements = len(elements)
            self.status_var.set(f"Processed {num_elements} elements successfully.")
        except Exception as e:
            print(f"Error formatting results: {e}")
            self.results_text.insert(tk.END, f"Error formatting results: {str(e)}")
            self.status_var.set("Error displaying results.")
    
    def _insert_large_text(self, text_widget, text):
        """Insert large text in chunks to prevent UI freezing."""
        chunk_size = 10000  # Characters per chunk
        
        # Create a function to insert text chunks and update the UI
        def insert_chunk(start_pos):
            if start_pos >= len(text):
                return
                
            end_pos = min(start_pos + chunk_size, len(text))
            chunk = text[start_pos:end_pos]
            
            text_widget.insert(tk.END, chunk)
            
            # Schedule the next chunk
            if end_pos < len(text):
                self.root.after(10, lambda: insert_chunk(end_pos))
                
        # Start inserting chunks
        insert_chunk(0)
    
    def copy_to_clipboard(self):
        """Copy the results to the clipboard."""
        if not self.elements:
            messagebox.showinfo("Info", "No results to copy. Process an SVG file first.")
            return
        
        try:
            # Clear clipboard and append new content
            self.root.clipboard_clear()
            self.root.clipboard_append(json.dumps(self.elements, indent=2))
            
            self.status_var.set("Results copied to clipboard!")
            
            # Optional: Flash the status bar to provide visual feedback
            original_bg = self.status_bar['background']
            self.status_bar.configure(background='#FFDD00')
            self.status_bar.configure(foreground='#111111')
            
            # Reset after a delay
            self.root.after(1000, lambda: self.status_bar.configure(background=original_bg, foreground='#FFDD00'))
            
        except tk.TclError as e:
            self.status_var.set("Error accessing clipboard.")
            messagebox.showerror("Clipboard Error", f"Clipboard access error: {str(e)}")
        except Exception as e:
            self.status_var.set("Error copying to clipboard.")
            messagebox.showerror("Clipboard Error", f"Error: {str(e)}")
    
    def save_to_file(self):
        """Save the results to a JSON file."""
        if not self.elements:
            messagebox.showinfo("Info", "No results to save. Process an SVG file first.")
            return
        
        try:
            # Get initial directory from the loaded SVG file
            initial_dir = os.path.dirname(self.file_path.get()) if self.file_path.get() else None
            
            # Generate a default filename based on the SVG filename
            default_filename = None
            if self.file_path.get():
                svg_basename = os.path.basename(self.file_path.get())
                svg_name = os.path.splitext(svg_basename)[0]
                default_filename = f"{svg_name}_elements.json"
            
            filetypes = [
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
            filename = filedialog.asksaveasfilename(
                title="Save Results",
                filetypes=filetypes,
                defaultextension=".json",
                initialdir=initial_dir,
                initialfile=default_filename
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(self.elements, f, indent=2)
                self.status_var.set(f"Results saved to {os.path.basename(filename)}")
                messagebox.showinfo("Success", f"Results have been saved to {filename}")
        except PermissionError:
            self.status_var.set("Error: Permission denied when saving file.")
            messagebox.showerror("Permission Error", "You don't have permission to save the file at this location.")
        except Exception as e:
            self.status_var.set("Error saving file.")
            messagebox.showerror("File Error", f"Error: {str(e)}")
    
    def clear_results(self):
        """Clear the results area."""
        self.results_text.delete(1.0, tk.END)
        self.elements = []
        self.status_var.set("Results cleared.")
        
        # Also clear the log text if it's getting too large
        if len(self.log_text.get(1.0, tk.END)) > 10000:  # If log is larger than ~10KB
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "[Log cleared to improve performance]\n")
    
    def on_closing(self):
        """
        Save configuration and close the window.
        
        This method is called when the window is closing.
        It saves the current configuration and destroys the window.
        """
        self._save_config_from_ui()
        self.root.destroy()

    def export_scada_project(self):
        """
        Export the processed SVG data as an Ignition SCADA project structure in a zip file.
        
        This method creates a zip file with the proper folder structure and
        configuration files for importing into Ignition SCADA.
        """
        if not self.elements:
            messagebox.showinfo("Info", "No results to export. Process an SVG file first.")
            return
        
        # Prevent export if processing is active
        if self.processing_thread_active:
            messagebox.showinfo("Processing", "Please wait for SVG processing to complete before exporting.")
            return
            
        # Validate SCADA project settings
        if not self._validate_scada_settings():
            return
            
        try:
            # Update UI to show exporting state
            self.status_var.set("Exporting SCADA project...")
            self.export_scada_button.configure(state=tk.DISABLED)
            self.progress.start()
            self.root.update_idletasks()
            
            # Ask for save location for the zip file
            project_folder_name = self._get_safe_project_name()
            zip_file_path = self._get_export_zip_path(project_folder_name)
            
            if not zip_file_path:
                self.status_var.set("Export cancelled.")
                self.progress.stop()
                self.export_scada_button.configure(state=tk.NORMAL)
                return
            
            # Create a thread for export to prevent UI freezing
            export_thread = threading.Thread(
                target=self._export_scada_thread,
                args=(zip_file_path, project_folder_name),
                daemon=True
            )
            export_thread.start()
                
        except Exception as e:
            self.status_var.set("Error preparing SCADA export.")
            messagebox.showerror("Export Error", f"Error: {str(e)}")
            self.progress.stop()
            self.export_scada_button.configure(state=tk.NORMAL)
    
    def _validate_scada_settings(self):
        """
        Validate the SCADA project settings.
        
        Returns:
            bool: True if settings are valid, False otherwise.
        """
        # Check for empty values
        required_fields = {
            'Project Title': self.project_title.get(),
            'Parent Project': self.parent_project.get(),
            'View Name': self.view_name.get(),
            'SVG URL': self.svg_url.get(),
        }
        
        empty_fields = [field for field, value in required_fields.items() if not value.strip()]
        
        if empty_fields:
            # Create the error message without using an f-string with a backslash in the expression
            error_msg = "The following fields cannot be empty:\n- " + "\n- ".join(empty_fields)
            messagebox.showerror(
                "Invalid Settings", 
                error_msg
            )
            return False
            
        # Validate numeric fields
        try:
            image_width = int(self.image_width.get())
            image_height = int(self.image_height.get())
            default_width = int(self.default_width.get())
            default_height = int(self.default_height.get())
            
            if any(dim <= 0 for dim in [image_width, image_height, default_width, default_height]):
                messagebox.showerror(
                    "Invalid Settings", 
                    "Width and height values must be positive integers."
                )
                return False
        except ValueError:
            messagebox.showerror(
                "Invalid Settings", 
                "Width and height values must be valid integers."
            )
            return False
            
        return True
    
    def _get_safe_project_name(self):
        """
        Get a safe project folder name based on the project title and current timestamp.
        
        Returns:
            str: A safe project folder name.
        """
        # Clean the project title to ensure it's a valid folder name
        project_title = self.project_title.get().strip()
        safe_title = re.sub(r'[^\w\-_]', '_', project_title)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
        
        return f"{safe_title}_{timestamp}"
    
    def _get_export_zip_path(self, project_folder_name):
        """
        Get the zip file path for the SCADA project export.
        
        Args:
            project_folder_name (str): The project folder name.
            
        Returns:
            str: The zip file path, or None if cancelled.
        """
        # Get initial directory from the loaded SVG file
        initial_dir = os.path.dirname(self.file_path.get()) if self.file_path.get() else None
        
        return filedialog.asksaveasfilename(
            title="Save SCADA Project Zip File",
            initialfile=f"{project_folder_name}.zip",
            initialdir=initial_dir,
            defaultextension=".zip",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
        )
    
    def _export_scada_thread(self, zip_file_path, project_folder_name):
        """Background thread for SCADA project export."""
        try:
            # Do the actual export
            self._create_scada_export_zip(zip_file_path, project_folder_name)
            
            # Update UI from main thread
            self.root.after(0, lambda: self._finish_export_success(zip_file_path))
        except Exception as exc:
            # Store error message
            error_message = str(exc)
            # Handle errors on the main thread
            self.root.after(0, lambda: self._finish_export_error(error_message))
    
    def _finish_export_success(self, zip_file_path):
        """Handle successful export completion in the main thread."""
        self.status_var.set(f"SCADA project exported to {os.path.basename(zip_file_path)}")
        messagebox.showinfo("Success", f"SCADA project has been exported to:\n{zip_file_path}")
        self.progress.stop()
        self.export_scada_button.configure(state=tk.NORMAL)
    
    def _finish_export_error(self, error_message):
        """Handle export error in the main thread."""
        self.status_var.set("Error exporting SCADA project.")
        messagebox.showerror("Export Error", f"Error: {error_message}")
        self.progress.stop()
        self.export_scada_button.configure(state=tk.NORMAL)
    
    def _create_scada_export_zip(self, zip_file_path, project_folder_name):
        """
        Create the SCADA project zip file with all required files.
        
        Args:
            zip_file_path (str): Path where the zip file will be saved
            project_folder_name (str): Name used for the zip file but not for internal folder structure
            
        Raises:
            Exception: If there's an error creating the zip file.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Create folder structure directly at temp_dir without the project folder level
                perspective_dir = os.path.join(temp_dir, "com.inductiveautomation.perspective")
                views_dir = os.path.join(perspective_dir, "views")
                detailed_views_dir = os.path.join(views_dir, "Detailed-Views")
                view_dir = os.path.join(detailed_views_dir, self.view_name.get())
                
                # Create all required directories
                os.makedirs(view_dir, exist_ok=True)
                
                # Create project.json
                self._create_project_json(temp_dir)
                
                # Create resource.json
                self._create_resource_json(view_dir)
                
                # Create empty thumbnail.png
                self._create_thumbnail(view_dir)
                
                # Create view.json with the processed elements
                self._create_view_json(view_dir)
                
                # Create the zip file
                with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Walk through the temporary directory and add all files to the zip
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculate the relative path for the zip file
                            rel_path = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, rel_path)
                
            except Exception:
                raise
    
    def _create_project_json(self, project_path):
        """
        Create the project.json file.
        
        Args:
            project_path (str): The path where project.json will be created.
            
        Raises:
            Exception: If there's an error creating the file.
        """
        project_config = {
            "title": self.project_title.get(),
            "description": "Generated by SVG Processor",
            "parent": self.parent_project.get(),
            "enabled": True,
            "inheritable": False
        }
        
        project_file = os.path.join(project_path, "project.json")
        with open(project_file, 'w') as f:
            json.dump(project_config, f, indent=2)
    
    def _create_resource_json(self, view_dir):
        """
        Create the resource.json file.
        
        Args:
            view_dir (str): The directory where resource.json will be created.
            
        Raises:
            Exception: If there's an error creating the file.
        """
        resource_config = {
            "scope": "G",
            "version": 1,
            "restricted": False,
            "overridable": True,
            "files": [
                "view.json",
                "thumbnail.png"
            ],
            "attributes": {
                "lastModification": {
                    "actor": "admin",
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "lastModificationSignature": "generated_by_svg_processor"
            }
        }
        
        resource_file = os.path.join(view_dir, "resource.json")
        with open(resource_file, 'w') as f:
            json.dump(resource_config, f, indent=2)
    
    def _create_thumbnail(self, view_dir):
        """
        Create an empty thumbnail.png file.
        
        Args:
            view_dir (str): The directory where thumbnail.png will be created.
            
        Raises:
            Exception: If there's an error creating the file.
        """
        thumbnail_file = os.path.join(view_dir, "thumbnail.png")
        empty_image = Image.new('RGBA', (950, 530), (240, 240, 240, 0))
        empty_image.save(thumbnail_file)
    
    def _create_view_json(self, view_dir):
        """
        Create the view.json file with the processed elements.
        
        Args:
            view_dir (str): The directory where view.json will be created.
            
        Raises:
            Exception: If there's an error creating the file.
        """
        # Convert dimensions to integers
        image_width = int(self.image_width.get())
        image_height = int(self.image_height.get())
        default_width = int(self.default_width.get())
        default_height = int(self.default_height.get())
        
        view_config = {
            "custom": {},
            "params": {},
            "props": {
                "defaultSize": {
                    "height": default_height,
                    "width": default_width
                }
            },
            "root": {
                "children": [],
                "meta": {
                    "name": "root"
                },
                "props": {
                    "style": {
                        "backgroundColor": "#FFFFFF"
                    }
                },
                "type": "ia.container.coord"
            }
        }
        
        # Add background SVG image as first child
        background_image = {
            "meta": {
                "name": "Image"
            },
            "position": {
                "height": image_height,
                "width": image_width
            },
            "propConfig": {
                "props.source": {
                    "binding": {
                        "config": {
                            "expression": "\"" + self.svg_url.get() + "?var\" + toMillis(now(100))"
                        },
                        "type": "expr"
                    }
                }
            },
            "props": {
                "fit": {
                    "mode": "fill"
                },
                "style": {
                    "backgroundColor": "#EEEEEE"
                }
            },
            "type": "ia.display.image"
        }
        
        view_config["root"]["children"].append(background_image)
        
        # Format the elements to match Ignition SCADA view format
        for element in self.elements:
            # Transform our element format to Ignition SCADA format
            scada_element = {
                "meta": {
                    "name": element["meta"]["name"]
                },
                "position": {
                    "height": element["position"]["height"],
                    "width": element["position"]["width"],
                    "x": element["position"]["x"],
                    "y": element["position"]["y"]
                },
                "props": {
                    "params": {
                        "directionLeft": element["props"]["params"]["directionLeft"],
                        "forceFaultStatus": element["props"]["params"]["forceFaultStatus"],
                        "forceRunningStatus": element["props"]["params"]["forceRunningStatus"],
                        "tagProps": element["props"]["params"]["tagProps"]
                    },
                    "path": element["props"]["path"]
                },
                "type": element["type"]
            }
            
            # Add rotation if specified in our app
            if "rotation" in element and element["rotation"]:
                scada_element["position"]["rotate"] = {
                    "angle": f"{element['rotation']}deg"
                }
            
            view_config["root"]["children"].append(scada_element)
        
        # Write view.json
        view_file = os.path.join(view_dir, "view.json")
        with open(view_file, 'w') as f:
            json.dump(view_config, f, indent=2)

def main():
    """
    Main entry point for the application.
    
    Creates the main application window and starts the Tkinter event loop.
    Handles any uncaught exceptions by showing an error message.
    """
    try:
        root = tk.Tk()
        app = SVGProcessorApp(root)
        
        # Add a simple confirmation dialog when closing with the X button
        def confirm_exit():
            if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
                app.on_closing()
        
        root.protocol("WM_DELETE_WINDOW", confirm_exit)
        
        # Center the window on the screen
        window_width = 1000
        window_height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
        
        root.mainloop()
        
    except Exception as e:
        # Show a messagebox with the error
        error_message = f"An error occurred while starting the application:\n{str(e)}"
        if 'root' not in locals() or not root:
            # If Tk hasn't been initialized yet, use print
            print(error_message)
        else:
            # If Tk is initialized, show a messagebox
            messagebox.showerror("Application Error", error_message)
        
        # Return non-zero exit code
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 