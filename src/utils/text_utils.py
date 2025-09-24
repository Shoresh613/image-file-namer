"""
Text processing and OCR utilities.
"""

import re
from typing import List

from ..config import OCR_CORRECTIONS


def fix_common_ocr_mistakes(text: str) -> str:
    """
    Fix common OCR mistakes in text.

    Args:
        text: Text with potential OCR mistakes

    Returns:
        Text with common mistakes corrected
    """
    # Apply predefined corrections
    for mistake, correction in OCR_CORRECTIONS.items():
        text = text.replace(mistake, correction)

    # Remove string of numbers followed by either K or M (for number of likes, views or hours ago)
    text = re.sub(r"\d+[KMh]", "", text)

    # Remove single characters that are not part of a word
    text = re.sub(r"\b\w\b", "", text)

    # Remove more than 1 consecutive space
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Remove string beginning with https or http
    text = re.sub(r"https?://\S+", "", text)

    return text


def remove_gibberish(text: str) -> str:
    """
    Remove potential OCR gibberish from text.

    Args:
        text: Text that may contain gibberish

    Returns:
        Text with gibberish removed
    """
    # Regex pattern for potential OCR gibberish
    pattern = r"\b(?!\w*'[a-z])(([qxzj]{2,})|([bcdfghjklmnpqrstvwxyz]*[aeiouy]{3,}[bcdfghjklmnpqrstvwxyz]*)|([aeiouy]*[bcdfghjklmnpqrstvwxyz]{5,}[aeiouy]*))\b"

    # Finding matches
    matches = re.findall(pattern, text)
    if matches:
        print("Potential OCR gibberish detected:", matches)

    # Removing gibberish
    cleaned_text = re.sub(pattern, "", text)
    return cleaned_text.strip()
