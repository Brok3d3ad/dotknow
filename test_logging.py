import argparse
from inkscape_transform import SVGTransformer

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Test the logging in SVG transformer')
    parser.add_argument('-s', '--svg', required=True, help='Path to SVG file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Create transformer with debug flag
    transformer = SVGTransformer(args.svg, debug=args.debug)
    
    # Process the SVG
    elements = transformer.process_svg()
    
    print(f"\nProcessed {len(elements)} elements")

if __name__ == "__main__":
    main() 