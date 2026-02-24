import os
import shutil
from pathlib import Path
from PIL import Image
from datetime import datetime

# Define directories
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"
ERROR_LOG_FILE = SCRIPT_DIR / "error_log.txt"

# Supported formats that don't need conversion
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp'}


def log_error(filename, filepath, error_message):
    """Log error with timestamp, filename, filepath, and error message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Filename: {filename} | Path: {filepath} | Error: {error_message}\n"
    
    try:
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as log_file:
            log_file.write(log_entry)
    except Exception as e:
        print(f"Failed to write to error log: {e}")


def get_output_filename(input_path, file_extension):
    """Determine the output filename based on input and whether conversion was needed."""
    filename = input_path.stem
    
    # If file extension is supported, keep original extension
    if file_extension.lower() in SUPPORTED_FORMATS:
        return f"{filename}{file_extension.lower()}"
    else:
        # For unsupported formats, convert to .jpeg
        return f"{filename}.jpeg"


def process_image(input_path):
    """Process a single image: convert if needed, resize, and save."""
    try:
        filename = input_path.name
        file_extension = input_path.suffix
        
        # Open the image
        try:
            img = Image.open(input_path)
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to open image: {str(e)}")
            return False
        
        # Convert to JPEG if necessary
        if file_extension.lower() not in SUPPORTED_FORMATS:
            try:
                # Convert RGBA to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            except Exception as e:
                log_error(filename, str(input_path), f"Failed to convert image mode: {str(e)}")
                return False
        
        # Resize image to 640x480 (stretch to fit)
        try:
            img_resized = img.resize((640, 480), Image.Resampling.LANCZOS)
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to resize image: {str(e)}")
            return False
        
        # Determine output filename
        output_filename = get_output_filename(input_path, file_extension)
        output_path = OUTPUT_DIR / output_filename
        
        # Save the resized image
        try:
            if output_filename.lower().endswith('.jpeg') or output_filename.lower().endswith('.jpg'):
                img_resized.save(output_path, 'JPEG', quality=95)
            elif output_filename.lower().endswith('.png'):
                img_resized.save(output_path, 'PNG')
            elif output_filename.lower().endswith('.bmp'):
                img_resized.save(output_path, 'BMP')
            else:
                img_resized.save(output_path)
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to save image: {str(e)}")
            return False
        
        # Delete the original image
        try:
            input_path.unlink()
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to delete original image: {str(e)}")
            return False
        
        print(f"✓ Processed: {filename} -> {output_filename}")
        return True
    
    except Exception as e:
        log_error(input_path.name, str(input_path), f"Unexpected error: {str(e)}")
        return False


def main():
    """Main function to process all images in the input folder."""
    print("Image Resizer with Format Conversion")
    print("=" * 50)
    
    # Check if input directory exists
    if not INPUT_DIR.exists():
        print(f"Error: Input directory does not exist at {INPUT_DIR}")
        return
    
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Get all files in input directory
    image_files = list(INPUT_DIR.iterdir())
    
    if not image_files:
        print(f"No files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(image_files)} file(s) in input directory\n")
    
    successful = 0
    failed = 0
    
    # Process each file
    for file_path in image_files:
        if file_path.is_file():
            if process_image(file_path):
                successful += 1
            else:
                failed += 1
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print(f"See {ERROR_LOG_FILE} for error details.")


if __name__ == "__main__":
    main()
