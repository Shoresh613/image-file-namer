"""
File and text utility functions.
"""

import os
import re
from typing import Set, Optional, List
from pathlib import Path

from ..config import ILLEGAL_CHARS, WORD_VARIANTS, WORDS_TO_REMOVE_FILE


def load_words_from_file(file_path: str) -> Optional[Set[str]]:
    """
    Load words from a text file, one word per line.

    Args:
        file_path: Path to the text file

    Returns:
        Set of words from the file, or None if file not found
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            words_set = {line.strip() for line in file if line.strip()}
            return words_set
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None


def count_image_files(directory: str) -> int:
    """
    Count the number of image files in a directory.

    Args:
        directory: Path to the directory

    Returns:
        Number of image files found
    """
    if not os.path.exists(directory):
        return 0

    files = os.listdir(directory)
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp")
    image_files = [file for file in files if file.lower().endswith(image_extensions)]
    return len(image_files)


def sanitize_filename_basic(filename: str) -> str:
    """
    Basic filename sanitization - removes illegal characters only.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename with illegal characters removed
    """
    # Remove illegal characters
    for char in ILLEGAL_CHARS:
        filename = filename.replace(char, "")

    # Replace multiple spaces with single space
    filename = re.sub(r" +", " ", filename)

    return filename.strip()


def remove_duplicate_words(text: str) -> str:
    """
    Remove duplicate words from text, handling case variations and similar words.

    This function removes duplicate words while preserving the first occurrence of each word.
    It handles:
    - Case insensitive duplicates (e.g., "COVID" and "covid")
    - Similar words like "vaccin" and "vaccine"
    - Simple plurals (e.g., "vaccine" and "vaccines")
    - Exact duplicates

    Args:
        text: The text from which to remove duplicate words

    Returns:
        Text with duplicate words removed
    """
    if not text or not text.strip():
        return text

    words = text.split()
    seen_words = set()
    result_words = []

    for word in words:
        if not word:  # Skip empty strings
            continue

        # Clean the word for comparison (remove punctuation, convert to lowercase)
        cleaned_word = re.sub(r"[^\w]", "", word.lower())

        if not cleaned_word:  # Skip if word becomes empty after cleaning
            continue

        # Check if this is a variant of a word we've already seen
        base_word = WORD_VARIANTS.get(cleaned_word, cleaned_word)

        # Also check for simple plurals (words ending in 's')
        singular_word = (
            base_word.rstrip("s")
            if base_word.endswith("s") and len(base_word) > 1
            else base_word
        )

        # Normalize to the most common form for comparison
        normalized_word = singular_word

        # Check if we've already seen this word (or its variants)
        if normalized_word not in seen_words:
            result_words.append(word)
            seen_words.add(normalized_word)

    return " ".join(result_words)


def clean_up_gpu_memory():
    """
    Frees up GPU memory by clearing PyTorch's cache and performing garbage collection.
    """
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            print("GPU memory cleaned up.")
        else:
            print("No GPU available to clean up.")
    except ImportError:
        print("PyTorch not available, skipping GPU cleanup.")


def check_time_in_string(text: str) -> Optional[int]:
    """
    Extract wait time from error message strings.

    Args:
        text: Error message text

    Returns:
        Number of seconds to wait, -1 for days, or None if no pattern found
    """
    # Search for the pattern "after [number] second" to know for how long to wait
    match = re.search(r"after (\d+) second", text)
    match_days = re.search(r"after (\d+) day", text)

    if match:
        seconds = int(match.group(1))
        return seconds
    elif match_days:
        return -1
    else:
        # If the pattern is not found, return None
        return None
