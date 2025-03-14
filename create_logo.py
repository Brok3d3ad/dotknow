from PIL import Image, ImageDraw, ImageFont
import os

def create_autstand_logo():
    # Create a black background image for the main logo
    width, height = 400, 200
    image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        # Try to load a bold font
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        # Fall back to default font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw "aut" in white
    draw.text((100, 80), "aut", fill='white', font=font_large)
    
    # Draw "Stand" in yellow
    draw.text((190, 80), "Stand", fill='#FFDD00', font=font_large)
    
    # Draw "Automation Standard" in smaller text
    draw.text((120, 150), "Automation Standard", fill='#FFDD00', font=font_small)
    
    # Save the image as JPG
    logo_path = "automation_standard_logo.jpg"
    image.save(logo_path, quality=95)
    print(f"Logo created and saved to {os.path.abspath(logo_path)}")
    
    # Create an improved icon that will be more readable in small sizes
    icon_size = 256
    icon_img = Image.new('RGB', (icon_size, icon_size), color='#000000')
    icon_draw = ImageDraw.Draw(icon_img)
    
    # Add a dark yellow square as background
    margin = 20
    icon_draw.rectangle(
        [(margin, margin), (icon_size - margin, icon_size - margin)],
        fill='#FFCC00'  # Brighter yellow for better visibility
    )
    
    # Try to load a bold font for the icon
    try:
        if os.name == 'nt':  # Windows
            # Check for common Windows fonts
            font_options = [
                "arialbd.ttf",  # Arial Bold
                "segoeui.ttf",  # Segoe UI
                "calibrib.ttf",  # Calibri Bold
                "arial.ttf"
            ]
            
            icon_font = None
            for font_file in font_options:
                try:
                    icon_font = ImageFont.truetype(font_file, 150)
                    break
                except:
                    pass
            
            # If no specific font found, try system font folder
            if not icon_font:
                icon_font = ImageFont.truetype("arial.ttf", 150)
        else:
            # For other OS
            icon_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 150)
    except:
        # Fallback to default if no fonts work
        icon_font = ImageFont.load_default()
    
    # Draw a simplified "aS" for better readability in small icon sizes
    icon_draw.text((icon_size//2-60, icon_size//2-80), "a", fill='#000000', font=icon_font)
    icon_draw.text((icon_size//2, icon_size//2-80), "S", fill='#000000', font=icon_font)
    
    # Save as PNG first for high quality
    temp_png = "temp_icon.png"
    icon_img.save(temp_png, format="PNG")
    
    # Also create ICO file
    icon_path = "autstand_icon.ico"
    try:
        # Convert PNG to ICO with multiple sizes for better display
        ico_img = Image.open(temp_png)
        # Save with multiple sizes for the ico file
        ico_img.save(icon_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Icon created and saved to {os.path.abspath(icon_path)}")
    except Exception as e:
        print(f"Error creating ICO file with multiple sizes: {e}")
        # Fallback to basic ICO conversion
        ico_img = Image.open(temp_png)
        ico_img.save(icon_path)
        print(f"Created basic icon at {os.path.abspath(icon_path)}")
    
    # Clean up temp file
    if os.path.exists(temp_png):
        os.remove(temp_png)
    
    return logo_path, icon_path

if __name__ == "__main__":
    create_autstand_logo() 