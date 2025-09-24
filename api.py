"""
Simple API interface for the Image File Namer.

This module provides a simplified interface for programmatic usage.
"""

from pathlib import Path
from typing import Union

from src import ImageFileNamer, BatchProcessor
from src.utils import setup_dependencies


class ImageFileNamerAPI:
    """
    Simple API interface for the Image File Namer.

    This class provides a simplified interface for common use cases.
    """

    def __init__(self, auto_setup: bool = True):
        """
        Initialize the API.

        Args:
            auto_setup: Automatically setup dependencies if True
        """
        self._namer = None
        self._batch_processor = None

        if auto_setup:
            setup_dependencies()

    @property
    def namer(self) -> ImageFileNamer:
        """Get or create the ImageFileNamer instance."""
        if self._namer is None:
            self._namer = ImageFileNamer()
        return self._namer

    @property
    def batch_processor(self) -> BatchProcessor:
        """Get or create the BatchProcessor instance."""
        if self._batch_processor is None:
            self._batch_processor = BatchProcessor()
        return self._batch_processor

    def rename_single_image(self, image_path: Union[str, Path]) -> str:
        """
        Generate a new filename for a single image.

        Args:
            image_path: Path to the image file

        Returns:
            Generated filename (without extension)
        """
        return self.namer.generate_new_filename(str(image_path))

    def process_folder(
        self,
        source_folder: Union[str, Path],
        target_folder: Union[str, Path],
        rate_limit: int = 100,
    ):
        """
        Process all images in a folder.

        Args:
            source_folder: Folder containing images to process
            target_folder: Folder to save renamed images
            rate_limit: Maximum images to process per minute
        """
        processor = BatchProcessor(rate_limit_per_minute=rate_limit)
        processor.process_images(source_folder, target_folder)


# Convenience functions for quick usage
def rename_image(image_path: Union[str, Path]) -> str:
    """
    Quick function to rename a single image.

    Args:
        image_path: Path to the image

    Returns:
        Generated filename
    """
    api = ImageFileNamerAPI()
    return api.rename_single_image(image_path)


def process_images(
    source_folder: Union[str, Path],
    target_folder: Union[str, Path],
    rate_limit: int = 100,
):
    """
    Quick function to process a folder of images.

    Args:
        source_folder: Source folder with images
        target_folder: Target folder for renamed images
        rate_limit: Processing rate limit
    """
    api = ImageFileNamerAPI()
    api.process_folder(source_folder, target_folder, rate_limit)
