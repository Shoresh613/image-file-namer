import os
from PIL import Image

def scale_image_horizontally(input_path, output_path):
    try:
        with Image.open(input_path) as img:
            # Get original dimensions
            original_width, original_height = img.size

            # Calculate new dimensions
            new_width = int(original_width * 0.5)
            new_height = original_height  # Unchanged

            # Resize the image
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)

            # Save the resized image as a JPEG
            resized_img.save(output_path, 'JPEG')
    except Exception as e:
        print(f"Failed to process {input_path}: {e}")

def process_directory(directory_path, output_directory):
    # Check if the output directory exists, if not, create it
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Process all files in the given directory
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
            input_path = os.path.join(directory_path, filename)
            output_path = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}.jpg")
            scale_image_horizontally(input_path, output_path)
            print(f"Processed {filename} into {output_path}")

# Specify the directory containing images and where to save them
source_directory = './images/scale_horizontally/'
target_directory = './images/scaled_horizontally/'

# Process all images in the directory
process_directory(source_directory, target_directory)
