import os
import json
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from create_update_script import merge_elements_to_view, create_default_view, create_batch_file

class SVGProcessingHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests from the HTML UI"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse the JSON data from the request
        request_data = json.loads(post_data)
        
        # Extract the data we need
        elements_json = request_data.get('elements', [])
        ignition_path = request_data.get('ignitionPath', '')
        
        try:
            # Create element.json file
            with open('element.json', 'w') as f:
                json.dump(elements_json, f, indent=2)
            print(f"Created element.json with {len(elements_json)} elements")
            
            # Process the file and path
            result = self.process_svg_to_ignition(ignition_path)
            
            # Return a success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow cross-origin requests
            self.end_headers()
            
            # Send the response
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            # Return an error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode('utf-8'))
            print(f"Error processing request: {e}")
            
    def process_svg_to_ignition(self, ignition_path):
        """Process the SVG and update the Ignition view"""
        temp_path = "temp_view.json"
        result_path = "updated_view.json"
        batch_file_path = "update_view.bat"
        
        try:
            # Step 1: Copy or create the view.json file
            if os.path.exists(ignition_path):
                print(f"Reading original view.json from: {ignition_path}")
                try:
                    import shutil
                    shutil.copy2(ignition_path, temp_path)
                    print(f"Original view.json copied to: {temp_path}")
                except Exception as copy_e:
                    print(f"Warning: Could not copy file: {copy_e}")
                    print("Creating a new file instead")
                    create_default_view(temp_path)
            else:
                print(f"Warning: Source view.json does not exist at {ignition_path}")
                print("Creating a new view.json file with default structure")
                create_default_view(temp_path)
            
            # Step 2: Merge the elements by appending to the existing view
            print("Appending SVG elements to the existing view...")
            merge_elements_to_view(temp_path)
            
            # Step 3: Rename the merged file to finalized result
            if os.path.exists(temp_path):
                import shutil
                shutil.move(temp_path, result_path)
                print(f"Updated view saved to: {result_path}")
            else:
                return {
                    'success': False,
                    'error': f"Expected {temp_path} to exist but it doesn't."
                }
            
            # Step 4: Create the batch file
            create_batch_file(result_path, ignition_path, batch_file_path)
            
            # Return success
            return {
                'success': True,
                'message': "Successfully processed SVG and created update files",
                'outputFiles': {
                    'element_json': os.path.abspath('element.json'),
                    'updated_view': os.path.abspath(result_path),
                    'batch_file': os.path.abspath(batch_file_path)
                }
            }
            
        except Exception as e:
            # Clean up temp files if there's an error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"Error in processing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=8000):
    """Run the server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SVGProcessingHandler)
    print(f"Server running at http://localhost:{port}")
    print(f"Open index.html in your browser and submit the form to process SVG files")
    httpd.serve_forever()

if __name__ == "__main__":
    # Check if port is provided as command-line argument
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number. Using default port {port}")
    
    run_server(port) 