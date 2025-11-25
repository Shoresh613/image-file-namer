"""
OCR and content analysis processor.
"""

import re

import ollama
from PIL import Image
import pytesseract

from ..config import (
    OLLAMA_MODEL_DESCRIPTION,
    OLLAMA_MODEL_KEYWORDS,
    OCR_LANGUAGES,
)


class ContentProcessor:
    """Handles OCR and content analysis for images."""

    def __init__(self):
        # No heavy initialization needed for pytesseract
        pass

    def extract_ocr_text(self, image_path: str) -> str:
        """
        Extract text from image using Tesseract OCR (multi-language).

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text from the image
        """
        print(f"Running Tesseract OCR on {image_path}...")
        try:
            image = Image.open(image_path)
            ocr_text = pytesseract.image_to_string(image, lang=OCR_LANGUAGES)
        except Exception as exc:
            print(f"Failed to run Tesseract on {image_path}: {exc}")
            return ""

        # Normalize whitespace while preserving spaces between words
        ocr_text = re.sub(r"[ \t]{2,}", " ", ocr_text)
        ocr_text = re.sub(r"\n{2,}", "\n", ocr_text).strip()
        print(f"OCR text via Tesseract:\n{ocr_text}\n")
        return ocr_text

    def get_image_description(self, image_path: str) -> str:
        """
        Get descriptive keywords for an image using local LLM.

        Args:
            image_path: Path to the image file

        Returns:
            Descriptive text for the image
        """
        response = ollama.chat(
            model=OLLAMA_MODEL_DESCRIPTION,
            messages=[
                {
                    "role": "user",
                    "content": "Output keywords for this image in one line for the purpose of giving the image file a name for easy search. Just a single space between keywords. No emojis.",
                    "images": [image_path],
                }
            ],
        )

        description = response["message"]["content"]
        print(f"Description of Image: {description}\n")
        return description

    def extract_keywords_from_text(self, ocr_text: str, description_text: str) -> str:
        """
        Extract relevant keywords from OCR and description text using LLM.

        Args:
            ocr_text: Text extracted from OCR
            description_text: Descriptive text about the image

        Returns:
            Selected keywords for filename
        """
        response = ollama.chat(
            model=OLLAMA_MODEL_KEYWORDS,
            messages=[
                {
                    "role": "user",
                    "content": "Out of the following words, pick 15 keywords that you think are most relevant for naming an image file. If you can't find 15, just pick the ones you think are most relevant. No other text in the reply, no motivations, just the keywords one after another in a single line with a single space between: "
                    + ocr_text
                    + " "
                    + description_text,
                }
            ],
        )

        keywords = response["message"]["content"]
        print(f"OCR and description keywords: {keywords}\n")
        return keywords
