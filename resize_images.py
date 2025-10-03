## Resize images in a directory to 50% of their original size (if larger than 600*600)
## and save them as JPEG files with 70% quality.

from PIL import Image
import os

# Set the source directory where your images are stored
source_directory = "./images/to_resize/"
# Set the target directory where you want to save the resized images
target_directory = "./images/resized/"

# Set amount of scaling (usually 0.5 for 50% reduction in size, or 0.75 for 75% reduction in size in case of X22 landscape screenshots)
scaling_factor = 0.50

# Create the target directory if it doesn't exist
if not os.path.exists(target_directory):
    os.makedirs(target_directory)


# Function to resize image
def resize_image(input_path, output_path):
    with Image.open(input_path) as img:
        # Check if the image is greater than 600x600 pixels
        if img.size[0] > 600 and img.size[1] > 600:
            new_size = (
                int(img.size[0] * scaling_factor),
                int(img.size[1] * scaling_factor),
            )
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)

            if resized_img.mode == "RGBA":
                resized_img = resized_img.convert("RGB")
            resized_img.save(output_path, "JPEG", quality=70)
            print(f"Resized {input_path} and saved to {output_path}")


# Iterate over all files in the source directory
for filename in os.listdir(source_directory):
    if filename.lower().endswith(
        (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp")
    ):
        input_path = os.path.join(source_directory, filename)
        base_filename = os.path.splitext(filename)[0]
        output_path = os.path.join(target_directory, f"{base_filename}.jpg")

        # Resize and save the image if applicable
        resize_image(input_path, output_path)

print("Image resizing is complete.")
