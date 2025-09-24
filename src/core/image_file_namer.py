"""
Main image file namer class that orchestrates the entire process.
"""

import random
from pathlib import Path
from typing import Optional

from ..processors import ContentProcessor, NERProcessor
from ..utils import (
    extract_date_from_ocr_text,
    extract_date_from_filename_or_timestamp,
    fix_common_ocr_mistakes,
    remove_gibberish,
)
from .filename_builder import FilenameBuilder


class ImageFileNamer:
    """
    Main class that orchestrates the image file naming process.

    This class combines OCR, content analysis, NER, date extraction,
    and filename generation into a single cohesive workflow.
    """

    def __init__(self, max_filename_length: int = 135):
        self.content_processor = ContentProcessor()
        self.ner_processor = NERProcessor()
        self.filename_builder = FilenameBuilder(max_filename_length)

    def generate_new_filename(self, image_path: str) -> str:
        """
        Generate a new filename for an image based on its content, recognized text, and descriptive elements.

        This function uses local LLM models (Ollama) and Docling OCR to analyze the content of an image
        and extract descriptive text and recognized printed text. It then processes this information to
        extract key phrases and generate a new, sanitized filename that reflects the content of the image.

        The function implements a date detection hierarchy:
        1. First tries to extract dates from OCR text within the image
        2. Falls back to extracting dates from the filename pattern
        3. Finally uses the file's modification timestamp as a last resort

        Args:
            image_path: The path to the image file to be analyzed.

        Returns:
            A new, sanitized filename derived from the content and text recognized in the image.
            The filename is optimized to maximize unique words within a 135 character limit for
            compatibility with various file systems and platforms.
        """
        # Extract OCR text from image
        ocr_text = self.content_processor.extract_ocr_text(image_path)

        # Get descriptive keywords for the image
        description_text = self.content_processor.get_image_description(image_path)

        # Extract date with priority: 1) OCR text, 2) filename, 3) file timestamp
        print("Extracting date with priority: OCR text -> filename -> timestamp")
        found_dates = extract_date_from_ocr_text(ocr_text)
        if found_dates:
            print(f"Date found in OCR text: {found_dates}")
        else:
            print("No date found in OCR text, checking filename and timestamp...")
            found_dates = extract_date_from_filename_or_timestamp(image_path)
            if found_dates:
                print(f"Date found in filename/timestamp: {found_dates}")
            else:
                print("No date found in filename or timestamp")

        # Extract keywords using LLM
        keywords = self.content_processor.extract_keywords_from_text(
            ocr_text, description_text
        )

        # Add back any words of people, places, organizations etc using NER
        ner_words = self.ner_processor.get_words_of_interest(ocr_text)
        print(f"Words of interest: {ner_words}")
        combined_keywords = ner_words + keywords

        # Clean up the text first (only character cleaning, not wordlist filtering)
        processed_text = fix_common_ocr_mistakes(remove_gibberish(combined_keywords))
        processed_text = self.filename_builder.sanitize_filename(processed_text)

        # Build optimized filename with incremental duplicate checking, wordlist filtering, and length management
        new_file_name = self.filename_builder.build_optimized_filename(
            words_text=processed_text,
            date_prefix=found_dates if found_dates else "",
            max_length=135,
        )

        # Fallback in case we end up with just the date or empty string
        if not new_file_name.strip() or (
            found_dates and new_file_name.strip() == found_dates.strip()
        ):
            new_file_name = self.filename_builder.create_fallback_filename(found_dates)

        return new_file_name
