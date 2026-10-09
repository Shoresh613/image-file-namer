"""
Main image file namer class that orchestrates the entire process.
"""

from typing import Any

from ..processors import ContentProcessor
from ..utils import (
    extract_date_from_ocr_text,
    extract_date_from_filename_or_timestamp,
)
from .filename_builder import FilenameBuilder


class ImageFileNamer:
    """
    Main class that orchestrates the image file naming process.

    This class combines:

    1. Tesseract OCR
    2. Image analysis through Lemonade
    3. Date extraction
    4. Compact filenames from image keywords only

    Only one Lemonade request is made per image.

    Date detection hierarchy:

    1. Date found in OCR text
    2. Date found in the existing filename
    3. File modification timestamp

    The selected date is passed separately to FilenameBuilder so that
    it remains at the beginning of the generated filename.
    """

    def __init__(
        self,
        max_filename_length: int = 135,
    ) -> None:
        self.max_filename_length = (
            max_filename_length
        )

        self.content_processor = (
            ContentProcessor()
        )

        self.filename_builder = (
            FilenameBuilder(
                max_filename_length
            )
        )

    @staticmethod
    def _value_to_text(
        value: Any,
    ) -> str:
        """
        Convert a string or collection of strings into plain text.

        This makes the code tolerant of NER and date helpers returning
        either a string, a list, a tuple or another simple value.
        """
        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return " ".join(
                str(item).strip()
                for item in value
                if item is not None
                and str(item).strip()
            )

        return str(value).strip()

    def generate_new_filename(
        self,
        image_path: str,
    ) -> str:
        """
        Generate a new filename for an image.

        The ContentProcessor first extracts OCR text and then performs one
        combined Lemonade request using both the image and OCR text.

        Date detection uses this priority:

        1. OCR text
        2. Existing filename
        3. File modification timestamp

        The detected date is supplied separately as ``date_prefix`` so that
        FilenameBuilder places it first in the resulting filename.

        Args:
            image_path:
                Path to the image file.

        Returns:
            A date prefix followed by image keywords in PascalCase.
        """
        print(
            f"\nProcessing image: {image_path}"
        )

        # Performs Tesseract OCR followed by one combined Lemonade request.
        ocr_text, image_keywords = (
            self.content_processor.process_image(
                image_path
            )
        )

        print(
            "Extracting date with priority: "
            "OCR text -> filename -> timestamp"
        )

        # First priority: dates visibly present inside the image.
        found_dates = extract_date_from_ocr_text(
            ocr_text
        )

        if found_dates:
            print(
                f"Date found in OCR text: "
                f"{found_dates}"
            )
        else:
            print(
                "No date found in OCR text. "
                "Checking filename and timestamp..."
            )

            # Second priority: an existing filename date.
            # Third priority: file modification timestamp.
            found_dates = (
                extract_date_from_filename_or_timestamp(
                    image_path
                )
            )

            if found_dates:
                print(
                    "Date found in filename or "
                    f"timestamp: {found_dates}"
                )
            else:
                print(
                    "No date found in OCR text, "
                    "filename, or timestamp."
                )

        # Only the model's selected keywords contribute to the filename.
        # Raw OCR is retained for the multimodal prompt and date extraction.
        # Normalize the result in case a date helper returns a collection
        # rather than a plain string.
        date_prefix = self._value_to_text(
            found_dates
        )

        # Passing the date separately ensures that it remains first.
        new_file_name = (
            self.filename_builder.build_keyword_filename(
                words_text=self._value_to_text(image_keywords),
                date_prefix=date_prefix,
                max_length=self.max_filename_length,
            )
        )

        normalized_filename = (
            new_file_name.strip()
        )

        normalized_date = (
            date_prefix.strip()
        )

        filename_is_empty = (
            not normalized_filename
        )

        filename_is_only_date = (
            bool(normalized_date)
            and normalized_filename
            == normalized_date
        )

        # Fallback if no usable content keywords survived cleanup.
        if (
            filename_is_empty
            or filename_is_only_date
        ):
            new_file_name = (
                self.filename_builder.create_fallback_filename(
                    date_prefix
                ).replace(" ", "")
            )

        print(
            f"Generated filename: "
            f"{new_file_name}\n"
        )

        return new_file_name
