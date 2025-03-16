import os
from PIL import Image
import cairosvg  # Make sure to install cairosvg for SVG conversion

def resize_and_copy_image(src_path, dest_path, target_size=(256, 256)):
    """
    Open an image from src_path, crop it (if it has a transparent border) by calculating
    its non-transparent bounding box, resize it while preserving its aspect ratio using the 
    LANCZOS filter, and paste it onto a transparent canvas of target_size.
    Save the final image as a PNG at dest_path.
    """
    try:
        img = Image.open(src_path)
    except Exception as e:
        print(f"Error opening {src_path}: {e}")
        return False

    # Ensure image has an alpha channel (RGBA)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    
    # Crop the image if it has transparent borders
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    
    # Resize image while preserving aspect ratio using LANCZOS
    img.thumbnail(target_size, Image.LANCZOS)
    
    # Create a transparent canvas with the target size
    new_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    
    # Calculate position to center the image on the canvas
    img_w, img_h = img.size
    offset = ((target_size[0] - img_w) // 2, (target_size[1] - img_h) // 2)
    
    # Paste the resized image onto the transparent canvas using itself as a mask
    new_img.paste(img, offset, mask=img)
    
    try:
        new_img.save(dest_path)
        return True
    except Exception as e:
        print(f"Error saving {dest_path}: {e}")
        return False

def process_logos(source_folder, dest_folder, target_size=(224, 224)):
    """
    Process all logo files from source_folder and save cropped and resized copies with transparent 
    backgrounds into dest_folder. For SVG files, convert them to PNG.
    """
    os.makedirs(dest_folder, exist_ok=True)
    # Supported raster formats (including .webp)
    supported_raster = ('.png', '.jpg', '.jpeg', '.ico', '.webp')
    
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder, filename)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext in supported_raster:
            # Save output as PNG to support transparency
            dest_path = os.path.join(dest_folder, f"{name}.png")
            if not resize_and_copy_image(file_path, dest_path, target_size):
                print(f"Failed processing {filename}")
        elif ext == '.svg':
            # Convert SVG to PNG using cairosvg with the target dimensions
            dest_path = os.path.join(dest_folder, f"{name}.png")
            try:
                cairosvg.svg2png(url=file_path, write_to=dest_path,
                                 output_width=target_size[0],
                                 output_height=target_size[1])
            except Exception as e:
                print(f"Error processing SVG {filename}: {e}")
        else:
            print(f"Unsupported file type for {filename}")

if __name__ == "__main__":
    source_folder = "logos"          # Folder containing the original logos
    dest_folder = "logos_resized"      # Folder where processed copies will be saved
    target_size = (224, 224)           # Target size (width, height)
    process_logos(source_folder, dest_folder, target_size)
