"""
Batch processor for handling multiple images.
"""

import os
import time
from pathlib import Path
from collections import deque
from typing import Union
from tqdm import tqdm

from ..utils import count_image_files
from .image_file_namer import ImageFileNamer


class BatchProcessor:
    """
    Processes and renames image files from a source folder to a target folder with rate limiting.

    This class handles batch processing of images, including rate limiting, progress tracking,
    and error handling during the renaming process.
    """

    def __init__(self, rate_limit_per_minute: int = 100):
        self.rate_limit_per_minute = rate_limit_per_minute
        self.image_namer = ImageFileNamer()

    def process_images(
        self, source_folder: Union[str, Path], target_folder: Union[str, Path]
    ):
        """
        Process and rename image files from source to target folder.

        Args:
            source_folder: Path to the source folder containing images
            target_folder: Path to the target folder for processed images
        """
        source_folder = Path(source_folder)
        target_folder = Path(target_folder)

        # Ensure target folder exists
        target_folder.mkdir(parents=True, exist_ok=True)

        # Use a deque to track the timestamps of processed images
        timestamps = deque()

        # Calculate total number of files once
        total_files = count_image_files(str(source_folder))
        processed_files = 0

        # Define supported image extensions
        image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]

        for image_path in tqdm(
            source_folder.glob("*"),
            total=total_files,
            desc="Processing images",
            unit="image",
        ):
            # Process only image files
            if image_path.is_file() and image_path.suffix.lower() in image_extensions:
                current_time = time.time()
                print(
                    f"Processing {image_path} ({processed_files + 1} of {total_files})"
                )

                # Remove timestamps older than 61 seconds from the deque (+1 to be on the safe side)
                while timestamps and current_time - timestamps[0] > 61:
                    timestamps.popleft()

                # Check if processing limit has been reached
                if len(timestamps) >= self.rate_limit_per_minute:
                    sleep_time = 61 - (current_time - timestamps[0])
                    print(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds.")
                    time.sleep(sleep_time)
                    # After sleeping, update current time
                    current_time = time.time()

                # Proceed with processing
                try:
                    new_filename = self.image_namer.generate_new_filename(
                        str(image_path)
                    ).strip()
                    new_filename += image_path.suffix
                    new_path = target_folder / new_filename

                    # Rename (move) file to new location with a new name
                    try:
                        os.rename(image_path, new_path)
                        print(f"Processed: {new_path}")
                    except FileExistsError:
                        # Try with a suffix if file exists
                        name_stem = new_filename.rsplit(".", 1)[0]
                        extension = new_filename.rsplit(".", 1)[1]
                        new_filename_alt = f"{name_stem}_{image_path.suffix}"
                        new_path_alt = target_folder / new_filename_alt
                        try:
                            os.rename(image_path, new_path_alt)
                            print(
                                f"Processed (renamed due to conflict): {new_path_alt}"
                            )
                        except Exception as e:
                            print(f"Failed to process {image_path}: {e}")
                            continue

                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
                    continue

                # Log the timestamp of this processing
                timestamps.append(time.time())
                processed_files += 1

        print(f"Finished processing {processed_files} images.")
