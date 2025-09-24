"""
Named Entity Recognition processor using spaCy.
"""

import re
from typing import List

import spacy

from ..config import NER_CATEGORIES, SPACY_MODEL
from ..config import (
    NAMES_TO_INCLUDE_FILE,
    NON_PERSONAL_NAMES_TO_INCLUDE,
    WORDS_TO_INCLUDE_FILE,
)
from ..utils import load_words_from_file


class NERProcessor:
    """Handles Named Entity Recognition using spaCy."""

    def __init__(self):
        self.nlp = None
        self._load_model()

    def _load_model(self):
        """Load the spaCy model."""
        try:
            self.nlp = spacy.load(SPACY_MODEL)
        except OSError:
            print(f"spaCy model {SPACY_MODEL} not found. Please install it first.")
            raise

    def get_words_of_interest(self, text: str) -> str:
        """
        Extract words of interest from text using Named Entity Recognition and word lists.

        Args:
            text: Text to process

        Returns:
            Space-separated string of extracted words
        """
        if not self.nlp:
            return ""

        # Process text for NER
        doc = self.nlp(text)

        # Find words of interest based on NER categories
        words = [ent.text for ent in doc.ents if ent.label_ in NER_CATEGORIES]

        # Load custom word lists
        names = []
        names_list = load_words_from_file(str(NAMES_TO_INCLUDE_FILE))
        if names_list:
            names.extend(names_list)

        non_personal_list = load_words_from_file(str(NON_PERSONAL_NAMES_TO_INCLUDE))
        if non_personal_list:
            names.extend(non_personal_list)

        # Add names from word lists if they are present in the text
        for name in names:
            # Create a regex pattern for the name with word boundaries
            pattern = r"\b" + re.escape(name) + r"\b"

            # Use re.search() to find the pattern in the text
            if re.search(pattern, text, re.IGNORECASE):
                words.append(name)

        # Add words from the include file if they exist in the text
        words_to_include = load_words_from_file(str(WORDS_TO_INCLUDE_FILE))
        lower_case_text = text.lower()

        if words_to_include:
            for word in words_to_include:
                if word.lower() in lower_case_text:
                    words.append(word)

        # Remove duplicates and return
        words = list(set(words))
        result = " ".join(words)
        if result:
            result += " "  # Add trailing space for consistency with original

        return result
