"""
Configuration settings for the Image File Namer application.
"""

import os
from pathlib import Path

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
# Ollama GPU settings. ``num_gpu`` is the number of *model layers* to offload,
# not the number of physical GPUs. -1 asks Ollama to offload every layer that
# fits, which is required for a full-GPU model run on Strix Halo.
OLLAMA_MODEL_DESCRIPTION = "gemma4:26b-a4b-it-qat-gpu"
OLLAMA_MODEL_KEYWORDS = "gemma4:26b-a4b-it-qat-gpu"
OLLAMA_NUM_GPU = -1
OLLAMA_NUM_CPU = 28
# 64k covers high-resolution vision input plus OCR text. It is deliberately
# below this project's model limit (262144) to leave unified memory available
# for the desktop and avoid a driver-level OOM on Strix Halo.
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "65536"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "24h")
# Refuse to continue if Ollama reports that the loaded model is substantially
# in system RAM. Set to 0 only when deliberately allowing CPU/partial offload.
OLLAMA_REQUIRE_FULL_GPU = os.getenv("OLLAMA_REQUIRE_FULL_GPU", "1") != "0"
OLLAMA_MIN_VRAM_RATIO = float(os.getenv("OLLAMA_MIN_VRAM_RATIO", "0.98"))
OLLAMA_MIN_SECONDS_BETWEEN_CALLS = 1.0
OLLAMA_MAX_RETRIES = 2
OLLAMA_RETRY_BACKOFF_SECONDS = 2.0

# OCR language configuration (Tesseract language codes separated by '+')
OCR_LANGUAGES = "eng+swe+deu"

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
    "Bíden": "Biden",
    "Representalives": "Representatives",
}
