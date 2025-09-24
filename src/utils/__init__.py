"""
Utility functions package.
"""

from .file_utils import (
    load_words_from_file,
    count_image_files,
    sanitize_filename_basic,
    remove_duplicate_words,
    clean_up_gpu_memory,
    check_time_in_string,
)

from .text_utils import (
    fix_common_ocr_mistakes,
    remove_gibberish,
)

from .date_utils import (
    find_dates,
    extract_date_from_ocr_text,
    extract_date_from_filename_or_timestamp,
)

from .setup import (
    download_spacy_model,
    setup_dependencies,
)

__all__ = [
    "load_words_from_file",
    "count_image_files",
    "sanitize_filename_basic",
    "remove_duplicate_words",
    "clean_up_gpu_memory",
    "check_time_in_string",
    "fix_common_ocr_mistakes",
    "remove_gibberish",
    "find_dates",
    "extract_date_from_ocr_text",
    "extract_date_from_filename_or_timestamp",
    "download_spacy_model",
    "setup_dependencies",
]
