"""
Filename builder and optimizer.
"""

import re
import random
from typing import Set

from ..config import DEFAULT_MAX_FILENAME_LENGTH, WORD_VARIANTS
from ..utils import (
    load_words_from_file,
    sanitize_filename_basic,
    remove_duplicate_words,
)
from ..config import (
    WORDS_TO_REMOVE_FILE,
    WORDS_TO_INCLUDE_FILE,
    NAMES_TO_INCLUDE_FILE,
    NON_PERSONAL_NAMES_TO_INCLUDE,
)


class FilenameBuilder:
    """Handles filename generation and optimization."""

    def __init__(self, max_length: int = DEFAULT_MAX_FILENAME_LENGTH):
        self.max_length = max_length
        self._load_wordlists()

    def _load_wordlists(self):
        """Load all wordlists for filtering."""
        self.words_to_remove = set()
        self.words_to_include = set()
        self.names_to_include = set()
        self.non_personal_names = set()

        # Load words to remove
        words_list = load_words_from_file(str(WORDS_TO_REMOVE_FILE))
        if words_list:
            self.words_to_remove = {word.lower() for word in words_list if word}

        # Load words to include
        words_list = load_words_from_file(str(WORDS_TO_INCLUDE_FILE))
        if words_list:
            self.words_to_include = {word.lower() for word in words_list if word}

        # Load names to include
        names_list = load_words_from_file(str(NAMES_TO_INCLUDE_FILE))
        if names_list:
            self.names_to_include = {word.lower() for word in names_list if word}

        # Load non-personal names
        non_personal_list = load_words_from_file(str(NON_PERSONAL_NAMES_TO_INCLUDE))
        if non_personal_list:
            self.non_personal_names = {
                word.lower() for word in non_personal_list if word
            }

    def build_optimized_filename(
        self, words_text: str, date_prefix: str = "", max_length: int = None
    ) -> str:
        """
        Build an optimized filename by adding words incrementally while checking for duplicates,
        wordlist filters, and length constraints. This maximizes the number of unique words that can fit.

        Args:
            words_text: The text containing all potential words
            date_prefix: Optional date prefix to add at the beginning
            max_length: Maximum length for the final filename (uses instance default if None)

        Returns:
            Optimized filename with maximum unique words within length constraint
        """
        if max_length is None:
            max_length = self.max_length

        if not words_text or not words_text.strip():
            return date_prefix.strip() if date_prefix else ""

        # Start with date prefix if provided
        result_parts = [date_prefix] if date_prefix else []
        current_length = len(date_prefix) + (
            1 if date_prefix else 0
        )  # +1 for space after date

        # Split words and prepare for processing
        available_words = words_text.split()
        seen_words = set()

        # If we have a date prefix, add its words to seen_words to avoid duplication
        if date_prefix:
            for word in date_prefix.split():
                cleaned = re.sub(r"[^\w]", "", word.lower())
                if cleaned:
                    base_word = WORD_VARIANTS.get(cleaned, cleaned)
                    singular_word = (
                        base_word.rstrip("s")
                        if base_word.endswith("s") and len(base_word) > 1
                        else base_word
                    )
                    seen_words.add(singular_word)

        # Process each word
        for word in available_words:
            if not word:
                continue

            # Calculate what the new length would be
            word_length = len(word)
            space_needed = 1 if result_parts else 0  # Space before word (if not first)
            new_length = current_length + space_needed + word_length

            # Skip if it would exceed max length
            if new_length > max_length:
                continue

            # Clean the word for comparison
            cleaned_word = re.sub(r"[^\w]", "", word.lower())
            if not cleaned_word:
                continue

            # Check wordlists - skip if word should be removed
            if cleaned_word in self.words_to_remove:
                continue

            # Check if word is in include lists (if they exist and are not empty)
            # Words are kept if: they are in include lists OR no include lists exist OR word is not commonly filtered
            should_include = True
            has_include_lists = bool(
                self.words_to_include
                or self.names_to_include
                or self.non_personal_names
            )

            if has_include_lists:
                # Include if the word is specifically in one of the include lists
                # OR if the word is longer than 3 characters (likely meaningful content)
                # This allows both curated important words and substantial content words
                should_include = (
                    cleaned_word in self.words_to_include
                    or cleaned_word in self.names_to_include
                    or cleaned_word in self.non_personal_names
                    or len(cleaned_word) > 3
                )

            if not should_include:
                continue

            # Check for duplicates
            base_word = WORD_VARIANTS.get(cleaned_word, cleaned_word)
            singular_word = (
                base_word.rstrip("s")
                if base_word.endswith("s") and len(base_word) > 1
                else base_word
            )
            normalized_word = singular_word

            # Only add if we haven't seen this word before
            if normalized_word not in seen_words:
                result_parts.append(word)
                seen_words.add(normalized_word)
                current_length = new_length

        return " ".join(result_parts)

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing illegal characters and applying word filters.

        Args:
            filename: The original filename to be sanitized

        Returns:
            The sanitized filename with illegal characters replaced and specified words removed
        """
        # Basic character sanitization
        filename = sanitize_filename_basic(filename)

        # Remove duplicate words
        filename = remove_duplicate_words(filename)

        # Remove specified words using word boundaries
        for word in self.words_to_remove:
            regex_pattern = r"\s*\b" + re.escape(word) + r"\b\s*"
            filename = re.sub(regex_pattern, " ", filename, flags=re.IGNORECASE)

        # Clean up multiple spaces
        filename = re.sub(r" +", " ", filename)

        return filename.strip()

    def create_fallback_filename(self, date_prefix: str = "") -> str:
        """
        Create a fallback filename when no meaningful content is found.

        Args:
            date_prefix: Optional date prefix

        Returns:
            Fallback filename
        """
        fallback_name = f"unnamed{random.randint(0, 1000)}"
        if date_prefix:
            return f"{date_prefix} {fallback_name}"
        return fallback_name
