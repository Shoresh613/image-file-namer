#!/usr/bin/env python3
"""
Example: Basic usage of the Image File Namer API.
"""
from pathlib import Path
from api import ImageFileNamerAPI


def main():
    # Initialize the API
    print("Initializing Image File Namer...")
    api = ImageFileNamerAPI()

    # Example 1: Rename a single image
    print("\n📸 Example 1: Single image renaming")
    image_path = "./assets/20230422 United nypost America biden overthrow prompted Hunter false CIA letter States write Flynn campaign Mike signed deputy Morrell.jpg"

    if Path(image_path).exists():
        new_name = api.rename_single_image(image_path)
        print(f"Original: {Path(image_path).name}")
        print(f"Generated: {new_name}")
    else:
        print(f"Image not found: {image_path}")

    # Example 2: Process a folder of images
    print("\n📁 Example 2: Batch processing")
    source_folder = "./images/to_name"
    target_folder = "./images/named_images_example"

    if Path(source_folder).exists():
        print(f"Processing images from: {source_folder}")
        print(f"Saving renamed images to: {target_folder}")
        api.process_folder(source_folder, target_folder, rate_limit=50)
        print("✅ Batch processing completed!")
    else:
        print(f"Source folder not found: {source_folder}")


if __name__ == "__main__":
    main()
