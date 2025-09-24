"""
Configuration settings for the Image File Namer application.
"""

from pathlib import Path
from typing import List

# File paths and directories
WORDLISTS_DIR = Path("./wordlists")
NAMES_TO_INCLUDE_FILE = WORDLISTS_DIR / "names_to_include.txt"
NON_PERSONAL_NAMES_TO_INCLUDE = WORDLISTS_DIR / "non_personal_names_to_include.txt"
WORDS_TO_INCLUDE_FILE = WORDLISTS_DIR / "words_to_include.txt"
WORDS_TO_REMOVE_FILE = WORDLISTS_DIR / "words_to_remove.txt"

# Default directories
DEFAULT_SOURCE_FOLDER = "./images/to_name"
DEFAULT_TARGET_FOLDER = "./images/named_images"

# Processing settings
DEFAULT_MAX_FILENAME_LENGTH = 135
DEFAULT_RATE_LIMIT_PER_MINUTE = 100  # Since we're using local LLM

# SpaCy model settings
SPACY_MODEL = "en_core_web_sm"

# Named Entity Recognition categories
NER_CATEGORIES = [
    "PERSON",
    "NORP",  # Nationalities, religious/political groups
    "FAC",  # Facilities
    "ORG",  # Organizations
    "GPE",  # Countries, cities, states
    "LOC",  # Non-GPE locations
    "PRODUCT",  # Objects, vehicles, foods
    "EVENT",  # Named hurricanes, battles, wars
    "WORK_OF_ART",  # Titles of books, songs
]

# OCR and LLM settings
OLLAMA_MODEL_DESCRIPTION = "gemma3:4b-it-qat"
OLLAMA_MODEL_KEYWORDS = "gemma3:4b-it-qat"

# Date extraction patterns
DATE_PATTERNS = [
    r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)",  # YYYY-MM-DD
    r"(?<!\d)(20\d{6})(?!\d)",  # YYYYMMDD
    r"(?<!\d)(20\d{2}-\d{1,2}-\d{1,2})(?!\d)",  # YYYY-M-D or YYYY-MM-D
    r"(?<!\d)(\d{1,2}/\d{1,2}/20\d{2})(?!\d)",  # M/D/YYYY or MM/DD/YYYY
    r"(?<!\d)(\d{1,2}\.\d{1,2}\.20\d{2})(?!\d)",  # D.M.YYYY or DD.MM.YYYY
]

# Illegal filename characters
ILLEGAL_CHARS = r"<>:,.•=-\"/\\|?*βß<>%&\{\}[]()$!#@;^`~''" "„‚'´¨»«€£¥—_§±"

# Word variants for duplicate detection
WORD_VARIANTS = {
    "vaccin": "vaccine",
    "vaccination": "vaccine",
    "vaccinera": "vaccine",
    "vaccinerad": "vaccine",
    "ovaccinerade": "vaccine",
    "covid": "covid",
    "covid19": "covid",
    "coronavirus": "covid",
    "corona": "covid",
    "pandemic": "pandemic",
    "pandemi": "pandemic",
}

# OCR text replacements
OCR_CORRECTIONS = {
    "OAnon": "QAnon",
    "Trurnp": "Trump",
    "exarnple": "example",
    "ernptied": "emptied",
    "darnage": "damage",
    "Jirn": "Jim",
    "YouTuhe": "YouTube",
}
