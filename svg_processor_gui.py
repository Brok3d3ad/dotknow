import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import json
import os
import sys
import io
from contextlib import redirect_stdout
from incscape_transform import SVGTransformer
from PIL import Image, ImageTk  # For handling images

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
    """GUI Application for processing SVG files and copying results to clipboard."""
    
    def __init__(self, root):
        """Initialize the application UI."""
        self.root = root
        self.root.title("autStand SVG Processor")  # Updated title
        self.root.geometry("750x650")  # More compact window size
        self.root.minsize(550, 450)  # Smaller minimum size
        
        # Set window icon
        self.set_window_icon()
        
        # Apply black and yellow theme
        self.configure_theme()
        
        # Header with logo
        self.header_frame = ttk.Frame(root)
        self.header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Load and display the logo
        try:
            # Look specifically for the logo specified for in-app display
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "automation_standard_logo.jpg")
            if not os.path.exists(logo_path):
                # Try current directory
                if os.path.exists("automation_standard_logo.jpg"):
                    logo_path = "automation_standard_logo.jpg"
                else:
                    # We don't want to use the .ico file for the in-app logo
                    logo_path = None
            
            if logo_path and os.path.exists(logo_path):
                # Load and resize the image
                logo_img = Image.open(logo_path)
                # Calculate new dimensions while maintaining aspect ratio
                width, height = logo_img.size
                new_height = 50
                new_width = int(width * (new_height / height))
                logo_img = logo_img.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert to PhotoImage and keep reference
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                
                # Create a label to display the logo
                self.logo_label = ttk.Label(self.header_frame, image=self.logo_photo, background='#222222')
                self.logo_label.pack(side=tk.LEFT, padx=5, pady=5)
                
                # Add title text label
                self.title_label = ttk.Label(self.header_frame, text="SVG to JSON Processor", 
                                           font=("Arial", 14, "bold"), background='#222222', foreground='#FFDD00')
                self.title_label.pack(side=tk.LEFT, padx=10)
            else:
                # Fallback text title if logo not found
                self.title_label = ttk.Label(self.header_frame, text="autStand SVG Processor", 
                                           font=("Arial", 16, "bold"), background='#222222', foreground='#FFDD00')
                self.title_label.pack(side=tk.LEFT, padx=10)
                
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Fallback if logo loading fails
            self.title_label = ttk.Label(self.header_frame, text="autStand SVG Processor", 
                                       font=("Arial", 16, "bold"), background='#222222', foreground='#FFDD00')
            self.title_label.pack(side=tk.LEFT, padx=10)
        
        # Create a notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)  # Reduced padding
        
        # Create the main tab
        self.main_frame = ttk.Frame(self.notebook, padding=5)  # Reduced padding
        self.notebook.add(self.main_frame, text="Process SVG")
        
        # Create the log tab
        self.log_frame = ttk.Frame(self.notebook, padding=5)  # Reduced padding
        self.notebook.add(self.log_frame, text="Processing Log")
        
        # Set up the log area
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, height=18, 
                                                  bg="#111111", fg="#FFDD00")  # Dark bg, yellow text
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Redirect stdout to the log text widget
        self.redirect = RedirectText(self.log_text)
        
        # File selection section
        self.file_frame = ttk.Frame(self.main_frame)
        self.file_frame.pack(fill=tk.X, pady=3)  # Reduced padding
        
        self.file_label = ttk.Label(self.file_frame, text="SVG File:")
        self.file_label.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.file_path = tk.StringVar()
        self.file_entry = ttk.Entry(self.file_frame, textvariable=self.file_path, width=45)  # Slightly smaller
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)  # Reduced padding
        
        self.browse_button = ttk.Button(self.file_frame, text="Browse...", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        # Options section - Add custom fields for JSON properties
        self.options_frame = ttk.LabelFrame(self.main_frame, text="JSON Output Options")
        self.options_frame.pack(fill=tk.X, pady=5, padx=3)  # Reduced padding
        
        # Element type option
        self.type_frame = ttk.Frame(self.options_frame)
        self.type_frame.pack(fill=tk.X, pady=2, padx=3)  # Reduced padding
        
        self.type_label = ttk.Label(self.type_frame, text="Element Type:")
        self.type_label.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.element_type = tk.StringVar(value="ia.display.view")
        self.type_entry = ttk.Entry(self.type_frame, textvariable=self.element_type, width=30)
        self.type_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)  # Reduced padding
        
        # Props path option
        self.path_frame = ttk.Frame(self.options_frame)
        self.path_frame.pack(fill=tk.X, pady=2, padx=3)  # Reduced padding
        
        self.path_label = ttk.Label(self.path_frame, text="Props Path:")
        self.path_label.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.props_path = tk.StringVar(value="Symbol-Views/Equipment-Views/Status")
        self.path_entry = ttk.Entry(self.path_frame, textvariable=self.props_path, width=40)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)  # Reduced padding
        
        # Dimension options in a more compact layout
        self.dim_frame = ttk.Frame(self.options_frame)
        self.dim_frame.pack(fill=tk.X, pady=2, padx=3)  # Reduced padding
        
        self.width_label = ttk.Label(self.dim_frame, text="Width:")
        self.width_label.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.element_width = tk.StringVar(value="14")
        self.width_entry = ttk.Entry(self.dim_frame, textvariable=self.element_width, width=6)  # Smaller width
        self.width_entry.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.height_label = ttk.Label(self.dim_frame, text="Height:")
        self.height_label.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.element_height = tk.StringVar(value="14")
        self.height_entry = ttk.Entry(self.dim_frame, textvariable=self.element_height, width=6)  # Smaller width
        self.height_entry.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        # Process button with progress indicator
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        self.process_button = ttk.Button(self.button_frame, text="Process SVG", command=self.process_svg)
        self.process_button.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.progress = ttk.Progressbar(self.button_frame, mode='indeterminate', length=180)  # Reduced length
        self.progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Results area
        self.results_label = ttk.Label(self.main_frame, text="Results:")
        self.results_label.pack(anchor=tk.W, pady=(5, 2))  # Reduced padding
        
        # Results Text widget without scrollbars
        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD, height=16,
                                   bg="#111111", fg="#FFDD00",
                                   highlightthickness=0, bd=1)  # Remove scrollbars
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Action buttons
        self.action_frame = ttk.Frame(self.main_frame)
        self.action_frame.pack(fill=tk.X, pady=3)  # Reduced padding
        
        self.copy_button = ttk.Button(self.action_frame, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.save_button = ttk.Button(self.action_frame, text="Save to File", command=self.save_to_file)
        self.save_button.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        self.clear_button = ttk.Button(self.action_frame, text="Clear Results", command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Store the processed elements
        self.elements = []
    
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
            # Prioritize the autStand_ic0n.ico file for the window/tray icon
            icon_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "autStand_ic0n.ico"),
                "autStand_ic0n.ico",  # Try current directory with exact case
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "autstand_icon.ico"),
                "autstand_icon.ico"   # Fallback to alternate case
            ]
            
            # Try each path until we find a valid icon file
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    # For Windows, we can use .ico files directly
                    if icon_path.endswith('.ico'):
                        self.root.iconbitmap(icon_path)
                        print(f"Set window icon from: {icon_path}")
                        return
            
            # Only if .ico files are not found, fall back to using the jpg logo as icon
            jpg_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "automation_standard_logo.jpg"),
                "automation_standard_logo.jpg"
            ]
            
            for icon_path in jpg_paths:
                if os.path.exists(icon_path):
                    # Convert .jpg to PhotoImage for icon
                    icon_img = Image.open(icon_path)
                    # Resize to standard icon size
                    icon_img = icon_img.resize((32, 32), Image.LANCZOS)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.root.iconphoto(True, icon_photo)
                    # Keep a reference to prevent garbage collection
                    self.icon_photo = icon_photo
                    print(f"Set window icon from: {icon_path}")
                    return
            
            print("No suitable icon file found for window icon")
        except Exception as e:
            print(f"Error setting window icon: {e}")
    
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
            custom_options = {
                'type': self.element_type.get(),
                'props_path': self.props_path.get(),
                'width': int(self.element_width.get()),
                'height': int(self.element_height.get())
            }
            
            # Process the SVG file with stdout redirected to log
            with redirect_stdout(self.redirect):
                transformer = SVGTransformer(svg_path, custom_options)
                self.elements = transformer.process_svg()
            
            # Display the results
            formatted_json = json.dumps(self.elements, indent=2)
            self.results_text.insert(tk.END, formatted_json)
            
            num_elements = len(self.elements)
            self.status_var.set(f"Processed {num_elements} elements successfully.")
            
            # Show the log tab to display the processing details
            #self.notebook.select(1)  # Switch to the log tab
            
            # After a delay, switch back to the main tab
            self.root.after(3000, lambda: self.notebook.select(0))
            
        except Exception as e:
            self.status_var.set("Error processing file.")
            messagebox.showerror("Processing Error", f"Error: {str(e)}")
        finally:
            self.progress.stop()
            self.process_button.configure(state=tk.NORMAL)
    
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
            #messagebox.showinfo("Success", "Results have been copied to the clipboard.")
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

def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = SVGProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 