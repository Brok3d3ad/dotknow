import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import json
import os
import sys
import io
import shutil
import zipfile
import tempfile
from datetime import datetime
from contextlib import redirect_stdout
from inkscape_transform import SVGTransformer
from PIL import Image, ImageTk  # For handling images

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
    """Handles loading, saving, and accessing application configuration."""
    
    def __init__(self, config_file=None):
        """Initialize the configuration manager."""
        self.config_dir = get_application_path()
        self.config_file = config_file or os.path.join(self.config_dir, "app_config.json")
        self.config = self._load_or_create_config()
        
    def _load_or_create_config(self):
        """Load existing config or create default if none exists."""
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        if not os.path.exists(self.config_file):
            return self._create_default_config()
        
        try:
            with open(self.config_file, 'r') as config_file:
                return json.load(config_file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return self._create_default_config()
    
    def _create_default_config(self):
        """Create and save default configuration."""
        try:
            with open(self.config_file, 'w') as config_file:
                json.dump(DEFAULT_CONFIG, config_file, indent=4)
            print(f"Created default configuration file at {self.config_file}")
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error creating default configuration file: {e}")
            return DEFAULT_CONFIG.copy()
    
    def save_config(self, updated_config):
        """Save the current configuration to file."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as config_file:
                json.dump(updated_config, config_file, indent=4)
            self.config = updated_config
            print(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_config(self):
        """Get a copy of the current configuration."""
        return self.config.copy()
    
    def get_value(self, key, default=None):
        """Get a specific configuration value."""
        return self.config.get(key, default)

class RedirectText:
    """Redirect stdout to a tkinter widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = io.StringIO()
        
    def write(self, string):
        self.buffer.write(string)
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # Auto-scroll to the end
        self.text_widget.update_idletasks()
    
    def flush(self):
        pass

class SVGProcessorApp:
    """Main application class for the SVG Processor."""
    
    def __init__(self, root, config_manager=None, svg_transformer_class=SVGTransformer):
        """Initialize the application."""
        self.root = root
        self.root.title("SVG Processor")
        self.root.minsize(800, 600)
        self.root.geometry("1000x700")
        
        # Dependency injection for easier testing
        self.config_manager = config_manager or ConfigManager()
        self.svg_transformer_class = svg_transformer_class
        
        # Configure the theme
        self.configure_theme()
        
        # Set window icon
        self.set_window_icon()
        
        # Initialize UI components
        self._init_ui_variables()
        self._create_form_frame()
        self._create_scada_frame()
        self._create_button_frame()
        self._create_notebook()
        self._create_status_bar()
        
        # Store the processed elements
        self.elements = []
        
        # Load saved configuration
        self._load_config_to_ui()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
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
        """Set the window icon to the autStand logo."""
        try:
            # Check which platform we're on
            is_windows = sys.platform.startswith('win')
            print(f"Platform is Windows: {is_windows}")
            
            # Get the application path for debugging
            app_path = get_application_path()
            print(f"Application path: {app_path}")
            
            # List files in the application path
            try:
                print(f"Files in application path: {os.listdir(app_path)}")
            except Exception as e:
                print(f"Could not list files in application path: {e}")
            
            # Prioritize the autStand_ic0n.ico file for the window/tray icon
            icon_paths = [
                os.path.join(app_path, "autStand_ic0n.ico"),
                "autStand_ic0n.ico",  # Try current directory with exact case
                os.path.join(app_path, "autstand_icon.ico"),
                "autstand_icon.ico",   # Fallback to alternate case
                os.path.abspath("autStand_ic0n.ico"),  # Try absolute path
                os.path.abspath("autstand_icon.ico")   # Try absolute path with alternate case
            ]
            
            print(f"Checking icon paths: {icon_paths}")
            
            # Try each path until we find a valid icon file
            for icon_path in icon_paths:
                print(f"Checking icon path: {icon_path}, exists: {os.path.exists(icon_path)}")
                if os.path.exists(icon_path):
                    # For Windows, we can use .ico files directly
                    if icon_path.endswith('.ico'):
                        if is_windows:
                            print(f"Using iconbitmap with: {icon_path}")
                            self.root.iconbitmap(icon_path)
                            print(f"Set window icon from: {icon_path}")
                            return
                        else:
                            # For non-Windows, convert .ico to PhotoImage
                            try:
                                print(f"Converting .ico to PhotoImage: {icon_path}")
                                icon_img = Image.open(icon_path)
                                # Resize to standard icon size
                                icon_img = icon_img.resize((32, 32), Image.LANCZOS)
                                icon_photo = ImageTk.PhotoImage(icon_img)
                                self.root.iconphoto(True, icon_photo)
                                print(f"Set window icon from: {icon_path}")
                                return
                            except Exception as ico_e:
                                print(f"Could not use .ico file on non-Windows platform: {ico_e}")
            
            print("No .ico files found, trying jpg files...")
            # Only if .ico files are not found, fall back to using the jpg logo as icon
            jpg_paths = [
                os.path.join(app_path, "automation_standard_logo.jpg"),
                "automation_standard_logo.jpg"
            ]
            
            for icon_path in jpg_paths:
                if os.path.exists(icon_path):
                    try:
                        # Convert .jpg to PhotoImage for icon
                        icon_img = Image.open(icon_path)
                        # Resize to standard icon size
                        icon_img = icon_img.resize((32, 32), Image.LANCZOS)
                        icon_photo = ImageTk.PhotoImage(icon_img)
                        
                        if is_windows:
                            # Windows can use both methods
                            try:
                                self.root.iconphoto(True, icon_photo)
                            except AttributeError:
                                # Older tkinter versions on Windows might not have iconphoto
                                # In this case we skip setting the icon from JPG
                                print("Could not set JPG icon on Windows (older tkinter)")
                        else:
                            # Non-Windows platforms use iconphoto
                            self.root.iconphoto(True, icon_photo)
                            
                        print(f"Set window icon from: {icon_path}")
                        return
                    except Exception as jpg_e:
                        print(f"Could not process JPG for icon: {jpg_e}")
            
            print("No suitable icon file found for window icon")
        except Exception as e:
            print(f"Error setting window icon: {e}")
    
    def _load_config_to_ui(self):
        """Load configuration values into UI elements."""
        config = self.config_manager.get_config()
        
        # Update form fields with saved values
        if config.get('file_path'):
            self.file_path.set(config['file_path'])
            
        if config.get('element_type'):
            self.element_type.set(config['element_type'])
            
        if config.get('props_path'):
            self.props_path.set(config['props_path'])
            
        if config.get('element_width'):
            self.element_width.set(config['element_width'])
            
        if config.get('element_height'):
            self.element_height.set(config['element_height'])
            
        if config.get('project_title'):
            self.project_title.set(config['project_title'])
            
        if config.get('parent_project'):
            self.parent_project.set(config['parent_project'])
            
        if config.get('view_name'):
            self.view_name.set(config['view_name'])
            
        if config.get('svg_url'):
            self.svg_url.set(config['svg_url'])
            
        if config.get('image_width'):
            self.image_width.set(config['image_width'])
            
        if config.get('image_height'):
            self.image_height.set(config['image_height'])
            
        if config.get('default_width'):
            self.default_width.set(config['default_width'])
            
        if config.get('default_height'):
            self.default_height.set(config['default_height'])
    
    def _save_config_from_ui(self):
        """Save current UI values to configuration."""
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
    
    def browse_file(self):
        """Open a file dialog to select an SVG file."""
        filetypes = [
            ("SVG files", "*.svg"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Select SVG File",
            filetypes=filetypes
        )
        if filename:
            self.file_path.set(filename)
            self.status_var.set(f"Selected file: {os.path.basename(filename)}")
    
    def process_svg(self):
        """Process the selected SVG file and display results."""
        svg_path = self.file_path.get()
        
        if not svg_path:
            messagebox.showerror("Error", "Please select an SVG file first.")
            return
        
        if not os.path.exists(svg_path):
            messagebox.showerror("Error", f"File not found: {svg_path}")
            return
        
        try:
            # Clear previous results
            self.results_text.delete(1.0, tk.END)
            self.log_text.delete(1.0, tk.END)
            
            self.status_var.set("Processing...")
            self.progress.start()
            self.process_button.configure(state=tk.DISABLED)
            self.root.update_idletasks()  # Update UI to show status change
            
            # Get custom options from form
            custom_options = self._get_processing_options()
            
            # Process the SVG file with stdout redirected to log
            elements = self._process_svg_file(svg_path, custom_options)
            self.elements = elements
            
            # Display the results
            self._display_results(elements)
            
            # After a delay, switch back to the main tab
            self.root.after(3000, lambda: self.notebook.select(0))
            
        except Exception as e:
            self.status_var.set("Error processing file.")
            messagebox.showerror("Processing Error", f"Error: {str(e)}")
        finally:
            self.progress.stop()
            self.process_button.configure(state=tk.NORMAL)
    
    def _get_processing_options(self):
        """Get processing options from the UI."""
        return {
            'type': self.element_type.get(),
            'props_path': self.props_path.get(),
            'width': int(self.element_width.get()),
            'height': int(self.element_height.get())
        }
    
    def _process_svg_file(self, svg_path, custom_options):
        """Process the SVG file and return the elements."""
        with redirect_stdout(self.redirect):
            transformer = self.svg_transformer_class(svg_path, custom_options)
            return transformer.process_svg()
    
    def _display_results(self, elements):
        """Display the processing results in the UI."""
        formatted_json = json.dumps(elements, indent=2)
        self.results_text.insert(tk.END, formatted_json)
        
        num_elements = len(elements)
        self.status_var.set(f"Processed {num_elements} elements successfully.")
    
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
        except Exception as e:
            self.status_var.set("Error copying to clipboard.")
            messagebox.showerror("Clipboard Error", f"Error: {str(e)}")
    
    def save_to_file(self):
        """Save the results to a JSON file."""
        if not self.elements:
            messagebox.showinfo("Info", "No results to save. Process an SVG file first.")
            return
        
        try:
            filetypes = [
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
            filename = filedialog.asksaveasfilename(
                title="Save Results",
                filetypes=filetypes,
                defaultextension=".json"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(self.elements, f, indent=2)
                self.status_var.set(f"Results saved to {os.path.basename(filename)}")
                messagebox.showinfo("Success", f"Results have been saved to {filename}")
        except Exception as e:
            self.status_var.set("Error saving file.")
            messagebox.showerror("File Error", f"Error: {str(e)}")
    
    def clear_results(self):
        """Clear the results area."""
        self.results_text.delete(1.0, tk.END)
        self.elements = []
        self.status_var.set("Results cleared.")
    
    def on_closing(self):
        """Save configuration and close the window."""
        self._save_config_from_ui()
        self.root.destroy()

    def export_scada_project(self):
        """Export the processed SVG data as an Ignition SCADA project structure in a zip file."""
        if not self.elements:
            messagebox.showinfo("Info", "No results to export. Process an SVG file first.")
            return
        
        try:
            # Ask for save location for the zip file
            project_folder_name = f"{self.project_title.get()}_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
            zip_file_path = filedialog.asksaveasfilename(
                title="Save SCADA Project Zip File",
                initialfile=f"{project_folder_name}.zip",
                defaultextension=".zip",
                filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
            )
            
            if not zip_file_path:
                messagebox.showinfo("Info", "Export cancelled.")
                return
            
            # Do the actual export
            self._create_scada_export_zip(zip_file_path, project_folder_name)
            
            self.status_var.set(f"SCADA project exported to {zip_file_path}")
            messagebox.showinfo("Success", f"SCADA project has been exported to:\n{zip_file_path}")
                
        except Exception as e:
            self.status_var.set("Error exporting SCADA project.")
            messagebox.showerror("Export Error", f"Error: {str(e)}")
    
    def _create_scada_export_zip(self, zip_file_path, project_folder_name):
        """Create the SCADA project zip file with all required files.
        
        Args:
            zip_file_path (str): Path where the zip file will be saved
            project_folder_name (str): Name used for the zip file but not for internal folder structure
        """
        with tempfile.TemporaryDirectory() as temp_dir:
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
                        # Calculate the relative path for the zip file - now directly from temp_dir
                        rel_path = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, rel_path)
    
    def _create_project_json(self, project_path):
        """Create the project.json file."""
        project_config = {
            "title": self.project_title.get(),
            "description": "Generated by SVG Processor",
            "parent": self.parent_project.get(),
            "enabled": True,
            "inheritable": False
        }
        
        with open(os.path.join(project_path, "project.json"), 'w') as f:
            json.dump(project_config, f, indent=2)
    
    def _create_resource_json(self, view_dir):
        """Create the resource.json file."""
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
        
        with open(os.path.join(view_dir, "resource.json"), 'w') as f:
            json.dump(resource_config, f, indent=2)
    
    def _create_thumbnail(self, view_dir):
        """Create an empty thumbnail.png file."""
        empty_image = Image.new('RGBA', (950, 530), (240, 240, 240, 0))
        empty_image.save(os.path.join(view_dir, "thumbnail.png"))
    
    def _create_view_json(self, view_dir):
        """Create the view.json file with the processed elements."""
        view_config = {
            "custom": {},
            "params": {},
            "props": {
                "defaultSize": {
                    "height": int(self.default_height.get()),
                    "width": int(self.default_width.get())
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
                "height": int(self.image_height.get()),
                "width": int(self.image_width.get())
            },
            "propConfig": {
                "props.source": {
                    "binding": {
                        "config": {
                            "expression": f"\"{self.svg_url.get()}?var\" + toMillis(now(100))"
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
            if hasattr(element, "rotation") and element["rotation"]:
                scada_element["position"]["rotate"] = {
                    "angle": f"{element['rotation']}deg"
                }
            
            view_config["root"]["children"].append(scada_element)
        
        # Write view.json
        with open(os.path.join(view_dir, "view.json"), 'w') as f:
            json.dump(view_config, f, indent=2)

def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = SVGProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 