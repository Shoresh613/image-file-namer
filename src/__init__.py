"""
Image File Namer - A modular system for intelligently renaming image files.

This package provides intelligent image file renaming capabilities using:
- OCR text extraction via Docling
- Content analysis via local LLM (Ollama)
- Named Entity Recognition via spaCy
- Smart date detection from multiple sources
- Optimized filename generation with deduplication and filtering
"""

from .core import ImageFileNamer, BatchProcessor, FilenameBuilder
from .processors import ContentProcessor, NERProcessor
from .utils import (
    clean_up_gpu_memory,
    extract_date_from_ocr_text,
    extract_date_from_filename_or_timestamp,
)

__version__ = "1.0.0"
__author__ = "Mikael Folkesson"

__all__ = [
    "ImageFileNamer",
    "BatchProcessor",
    "FilenameBuilder",
    "ContentProcessor",
    "NERProcessor",
    "clean_up_gpu_memory",
    "extract_date_from_ocr_text",
    "extract_date_from_filename_or_timestamp",
]
