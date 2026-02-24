import os
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from datetime import datetime
from pysstv.color import ScottieS1

# Define directories
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"
ERROR_LOG_FILE = SCRIPT_DIR / "error_log.txt"

# Supported formats that don't need conversion
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp'}

# SSTV configuration
SAMPLE_RATE = 48000  # 48000 Hz for better decoder compatibility
DEFAULT_CALLSIGN = ""  # Optional: Set to your callsign for FSKID identification

# Image quality optimization parameters
CONTRAST_MULTIPLIER = 1.4   # Enhance contrast for better frequency spread (standard: 1.4)
SATURATION_MULTIPLIER = 1.15  # Boost saturation for better color separation (standard: 1.15)
GAMMA_CORRECTION = 0.45     # Gamma correction to restore shadow detail (standard: 0.45)
DENOISE_RADIUS = 0.7        # Light noise reduction to clean up artifacts (standard: 0.7)


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


def optimize_image_quality(img):
    """Apply professional-grade image optimization for SSTV transmission.
    
    Optimizations applied:
    - Contrast enhancement (1.4x): Expands frequency range for robustness
    - Saturation boost (1.15x): Better color separation in transmission
    - Gamma correction (0.45): Restores shadow detail
    - Light noise reduction: Cleans up compression artifacts
    
    Args:
        img: PIL Image object in RGB mode
        
    Returns:
        Optimized PIL Image object
    """
    # 1. Enhance contrast for better frequency spread
    # SSTV uses 1500-2300 Hz (800 Hz span). Higher contrast = wider frequency spread = more robust
    contrast_enhancer = ImageEnhance.Contrast(img)
    img = contrast_enhancer.enhance(CONTRAST_MULTIPLIER)
    
    # 2. Boost saturation for better color separation
    # Helps distinguish colors in limited 800 Hz bandwidth
    color_enhancer = ImageEnhance.Color(img)
    img = color_enhancer.enhance(SATURATION_MULTIPLIER)
    
    # 3. Apply gamma correction to restore shadow detail
    # Gamma 0.45 brightens midtones/shadows without clipping highlights
    import numpy as np
    img_array = np.array(img, dtype=np.float32) / 255.0
    img_array = np.power(img_array, GAMMA_CORRECTION)
    img_array = (img_array * 255).astype(np.uint8)
    img = Image.fromarray(img_array)
    
    # 4. Light noise reduction to clean up compression artifacts
    # Using SMOOTH filter (conservative, 0.7px equivalent)
    img = img.filter(ImageFilter.GaussianBlur(radius=DENOISE_RADIUS))
    
    # 5. Slight sharpening to compensate for blur and enhance details
    # SSTV bandwidth limitation means sharpening helps maintain clarity
    sharpness_enhancer = ImageEnhance.Sharpness(img)
    img = sharpness_enhancer.enhance(1.1)  # 10% sharpening
    
    return img


def convert_image_to_sstv(resized_image_path, output_filename_base, callsign=None):
    """Convert a resized image to SSTV WAV audio file with proper synchronization.
    
    Args:
        resized_image_path: Path to the resized image
        output_filename_base: Output filename without extension
        callsign: Optional callsign for FSKID identification signal
        
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
        
        # ScottieS1 requires specific dimensions: 320x256 pixels
        # If image is different size, resize it to ScottieS1 specifications
        if img.size != (320, 256):
            img = img.resize((320, 256), Image.Resampling.LANCZOS)
        
        # Apply quality optimization for best SSTV transmission
        img = optimize_image_quality(img)
        
        # Create SSTV encoder (ScottieS1 mode with 48000 Hz sample rate, 16-bit audio)
        sstv = ScottieS1(img, SAMPLE_RATE, 16)
        
        # Enable VOX (Voice) tones for proper decoder synchronization
        # VOX tones provide timing markers at the beginning of transmission
        sstv.vox_enabled = True
        
        # Add FSKID (FSK Identification) signal if callsign provided
        # FSKID helps receivers identify the transmission
        if callsign:
            sstv.add_fskid_text(callsign)
        
        # Generate WAV file
        output_wav_path = OUTPUT_DIR / f"{output_filename_base}.wav"
        
        # Write the SSTV signal to WAV file
        # This includes: VOX tones -> Calibration header -> VIS code -> Image data -> FSKID
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
        
        # Resize image to 320x256 (ScottieS1 SSTV requirements)
        try:
            img_resized = img.resize((320, 256), Image.Resampling.LANCZOS)
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to resize image: {str(e)}")
            return False
        
        # Save resized image to temporary location with high quality
        try:
            temp_image_path = Path(tempfile.gettempdir()) / f"sstv_temp_{base_filename}.jpg"
            # Use JPEG quality 99 to minimize compression loss during temporary save
            img_resized.save(temp_image_path, 'JPEG', quality=99)
        except Exception as e:
            log_error(filename, str(input_path), f"Failed to save temporary image: {str(e)}")
            return False
        
        # Convert resized image to SSTV WAV
        try:
            convert_image_to_sstv(temp_image_path, base_filename, DEFAULT_CALLSIGN)
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
    print(f"SSTV Mode: ScottieS1 (Color)")
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"VOX Tones: Enabled")
    if DEFAULT_CALLSIGN:
        print(f"FSKID Callsign: {DEFAULT_CALLSIGN}")
    print()
    
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
