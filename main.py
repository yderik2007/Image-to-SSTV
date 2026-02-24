import os
import shutil
import tempfile
from pathlib import Path
from PIL import Image
from datetime import datetime
from pysstv.color import PD120

# Define directories
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"
ERROR_LOG_FILE = SCRIPT_DIR / "error_log.txt"

# Supported formats that don't need conversion
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp'}

# SSTV configuration
SAMPLE_RATE = 44100  # 44100 Hz for standard WAV quality


def log_error(filename, filepath, error_message):
    """Log error with timestamp, filename, filepath, and error message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Filename: {filename} | Path: {filepath} | Error: {error_message}\n"
    
    try:
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as log_file:
            log_file.write(log_entry)
    except Exception as e:
        print(f"Failed to write to error log: {e}")


def get_base_filename(input_path, file_extension):
    """Get the base filename without extension for output."""
    filename = input_path.stem
    return filename


def convert_image_to_sstv(resized_image_path, output_filename_base):
    """Convert a resized image to SSTV WAV audio file.
    
    Args:
        resized_image_path: Path to the resized image
        output_filename_base: Output filename without extension
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load and prepare the image for SSTV encoding
        img = Image.open(resized_image_path)
        
        # Convert to RGB for color support (PD120 requires RGB)
        if img.mode != 'RGB':
            if img.mode == 'RGBA':
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            else:
                img = img.convert('RGB')
        
        # PD120 requires specific dimensions: 640x496 pixels
        # If image is different size, resize it to PD120 specifications
        if img.size != (640, 496):
            img = img.resize((640, 496), Image.Resampling.LANCZOS)
        
        # Create SSTV encoder (PD120 mode with 44100 Hz sample rate, 16-bit audio)
        sstv = PD120(img, SAMPLE_RATE, 16)
        
        # Generate WAV file
        output_wav_path = OUTPUT_DIR / f"{output_filename_base}.wav"
        
        # Write the SSTV signal to WAV file
        sstv.write_wav(str(output_wav_path))
        
        return True
    
    except Exception as e:
        raise Exception(f"Failed to convert to SSTV: {str(e)}")


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
    """Process a single image: convert if needed, resize, encode to SSTV WAV, and cleanup."""
    temp_image_path = None
    
    try:
        filename = input_path.name
        file_extension = input_path.suffix
        base_filename = get_base_filename(input_path, file_extension)
        
        # Open the image
        try:
            img = Image.open(input_path)
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to open image: {str(e)}")
            return False
        
        # Convert to appropriate format if necessary
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
        
        # Resize image to 640x496 (PD120 SSTV requirements)
        try:
            img_resized = img.resize((640, 496), Image.Resampling.LANCZOS)
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to resize image: {str(e)}")
            return False
        
        # Save resized image to temporary location
        try:
            temp_image_path = Path(tempfile.gettempdir()) / f"sstv_temp_{base_filename}.jpg"
            img_resized.save(temp_image_path, 'JPEG', quality=95)
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to save temporary image: {str(e)}")
            return False
        
        # Convert resized image to SSTV WAV
        try:
            convert_image_to_sstv(temp_image_path, base_filename)
        except Exception as e:
            log_error(filename, str(input_path), str(e))
            return False
        finally:
            # Clean up temporary image file
            if temp_image_path and temp_image_path.exists():
                try:
                    temp_image_path.unlink()
                except Exception as e:
                    log_error(filename, str(input_path), f"Failed to delete temporary image: {str(e)}")
        
        # Delete the original image from input folder
        try:
            input_path.unlink()
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to delete original image: {str(e)}")
            return False
        
        print(f"✓ Processed: {filename} -> {base_filename}.wav")
        return True
    
    except Exception as e:
        log_error(input_path.name, str(input_path), f"Unexpected error: {str(e)}")
        # Clean up temporary image if it exists
        if temp_image_path and temp_image_path.exists():
            try:
                temp_image_path.unlink()
            except:
                pass
        return False


def main():
    """Main function to process all images in the input folder."""
    print("Image to SSTV WAV Converter")
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
    
    print(f"Found {len(image_files)} file(s) in input directory")
    print(f"SSTV Mode: PD120 (Color)")
    print(f"Sample Rate: {SAMPLE_RATE} Hz\n")
    
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
    print(f"WAV files saved to: {OUTPUT_DIR}")
    
    if failed > 0:
        print(f"See {ERROR_LOG_FILE} for error details.")


if __name__ == "__main__":
    main()
