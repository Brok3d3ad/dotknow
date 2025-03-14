# SVG to Ignition View Converter

A web-based tool for selecting SVG files, extracting elements, and integrating them into Ignition View configurations.

## Features

- Select SVG files from your local system
- Automatically extract elements with IDs from SVG files
- Preview the selected SVG file before processing
- Specify the path to your Ignition View configuration file
- Server-side processing using Python
- Creates batch files for easy installation into Ignition

## How to Use

### Step 1: Start the Server

1. Make sure you have Python installed on your system
2. Open a command prompt or terminal
3. Navigate to the directory containing the project files
4. Run the server:
   ```
   python server.py
   ```
5. The server will start on port 8000 by default (you can specify a different port as an argument)

### Step 2: Open the Web Interface

1. Open `index.html` in any modern web browser
2. The interface will connect to the local server automatically

### Step 3: Process an SVG File

1. Click "Choose File" to select an SVG file from your computer
2. The SVG will be displayed in the preview area and elements will be extracted automatically
3. Enter the path to your Ignition View (the default path is pre-filled)
4. Click "Process SVG" to send the data to the server for processing
5. Wait for the server to process the file
6. If successful, you'll see information about the output files

### Step 4: Complete the Integration

1. Run the generated batch file as administrator
2. The batch file will copy the updated view to your Ignition installation directory
3. Open your Ignition Designer to see the updated view with the SVG elements

## System Requirements

- Python 3.6 or higher
- A modern web browser (Chrome, Firefox, Safari, Edge)
- Proper file permissions for accessing the Ignition installation directory

## Files Included

- `index.html`: The web interface for selecting SVG files and specifying paths
- `server.py`: Python server that processes requests from the web interface
- `create_update_script.py`: Core script for processing SVG files and updating Ignition views

## Technical Details

The system works by:

1. Extracting elements with IDs from the SVG file
2. Creating an element.json file with the extracted elements
3. Merging the elements into an existing view.json file or creating a new one
4. Generating a batch file to copy the updated view to the Ignition installation directory

## Troubleshooting

- **Server Connection Error**: Make sure the server is running and the server URL in the web interface is correct
- **Permission Errors**: The batch file must be run as administrator to write to the Ignition directory
- **No Elements Found**: The SVG file must have elements with ID attributes for proper extraction
- **Installation Failures**: Ensure Ignition is not using the file when you try to update it

## Customization

You can customize the default paths and behavior by:

1. Editing the default Ignition path in the HTML file
2. Modifying the element extraction logic in the JavaScript
3. Customizing the server port by passing it as an argument: `python server.py 8080` 