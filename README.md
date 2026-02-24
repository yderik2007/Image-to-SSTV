# Image-to-SSTV

A Python-based image processing tool for converting and resizing images to the optimal format for SSTV (Slow Scan Television) transmission.

## Features

- **Automatic Format Detection**: Identifies JPG, JPEG, PNG, and BMP formats
- **Smart Format Conversion**: Automatically converts unsupported image formats to JPEG
- **Image Resizing**: Resizes all images to 640x480 pixels (stretched to fit)
- **Batch Processing**: Processes all images in the input folder in one run
- **Automatic Cleanup**: Deletes original images from the input folder after successful processing
- **Error Logging**: Comprehensive logging with timestamps, filenames, file paths, and error details
- **Graceful Error Handling**: Continues processing remaining images even if some fail

## Project Structure

```
Image-to-SSTV-main/
├── input/              # Place images here for processing
├── output/             # Resized images are saved here
├── main.py             # Main processing script
├── requirements.txt    # Python dependencies
├── error_log.txt       # Error log file
└── README.md           # This file
```

## Installation

1. Clone or navigate to the project directory
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place your images in the `input/` folder
2. Run the script:
   ```bash
   python main.py
   ```
3. Check the `output/` folder for resized images
4. Review `error_log.txt` if any images failed to process

## Image Format Handling

- **Supported formats** (JPG, JPEG, PNG, BMP): Processed directly with original extension preserved
- **Unsupported formats** (GIF, TIFF, WebP, etc.): Converted to JPEG format with `.jpeg` extension

### Format Conversion Details

- JPEG files are saved with 95% quality for optimal balance between quality and file size
- PNG files with transparency are converted to RGB with a white background before resizing
- All images are resized using high-quality LANCZOS resampling

## Output

The script provides:
- **Console output**: Real-time processing status for each image
- **Summary statistics**: Number of successful and failed images
- **Error log**: Detailed information about any failed image processing attempts

Each error log entry includes:
- Timestamp (YYYY-MM-DD HH:MM:SS format)
- Filename
- Full file path
- Detailed error message

## Requirements

- Python 3.6+
- Pillow 10.1.0

## Notes

- The script processes images one batch at a time and exits upon completion
- Original images are permanently deleted after successful processing, so ensure you have backups if needed
- Empty the `output/` folder between runs to avoid confusion with previously processed images
