"""
Date extraction utilities.
"""

import datetime
import os
import re
from typing import Optional, List

from ..config import DATE_PATTERNS


def find_dates(text: str) -> List[str]:
    """
    Find dates in text using various patterns.

    Args:
        text: Text to search for dates

    Returns:
        List of found dates
    """
    matches = []
    for pattern in DATE_PATTERNS:
        found = re.findall(pattern, text)
        matches.extend(found)
    return matches


def extract_date_from_ocr_text(ocr_text: str) -> Optional[str]:
    """
    Extract the last (most recent or most relevant) date found in OCR text.

    Args:
        ocr_text: OCR extracted text

    Returns:
        Date in YYYYMMDD format, or None if no date found
    """
    if not ocr_text:
        return None

    found_dates = find_dates(ocr_text)

    if found_dates:
        # Take the last date found, as it's often the most relevant
        last_date = found_dates[-1]

        # Clean up the date format - remove separators and ensure YYYYMMDD format
        date_str = last_date.replace("-", "").replace("/", "").replace(".", "")

        # Handle different date formats found
        if len(date_str) == 8 and date_str.isdigit():  # YYYYMMDD
            return date_str
        elif len(date_str) == 6 and date_str.isdigit():  # YYMMDD, add 20 prefix
            return "20" + date_str
        else:
            # Try to parse other formats and convert to YYYYMMDD
            try:
                # Handle formats like MM/DD/YYYY or DD.MM.YYYY
                if "/" in last_date:
                    parts = last_date.split("/")
                    if len(parts) == 3:
                        month, day, year = parts
                        return f"{year}{month.zfill(2)}{day.zfill(2)}"
                elif "." in last_date:
                    parts = last_date.split(".")
                    if len(parts) == 3:
                        day, month, year = parts
                        return f"{year}{month.zfill(2)}{day.zfill(2)}"
                elif "-" in last_date and len(last_date.split("-")) == 3:
                    year, month, day = last_date.split("-")
                    return f"{year}{month.zfill(2)}{day.zfill(2)}"
            except:
                pass

    return None


def extract_date_from_filename_or_timestamp(image_path: str) -> Optional[str]:
    """
    Extract date from filename or file timestamp as fallback.

    Args:
        image_path: Path to the image file

    Returns:
        Date in YYYYMMDD format
    """
    # First try to find dates in the filename
    filename = str(image_path)
    found_dates = find_dates(filename)

    if found_dates:
        # Clean up the date format - remove separators and ensure YYYYMMDD format
        date_str = found_dates[0].replace("-", "").replace("/", "").replace(".", "")

        # Handle different date formats found
        if len(date_str) == 8 and date_str.isdigit():  # YYYYMMDD
            return date_str
        elif len(date_str) == 6 and date_str.isdigit():  # YYMMDD, add 20 prefix
            return "20" + date_str
        else:
            # Try to parse other formats and convert to YYYYMMDD
            try:
                # Handle formats like MM/DD/YYYY or DD.MM.YYYY
                original_date = found_dates[0]
                if "/" in original_date:
                    parts = original_date.split("/")
                    if len(parts) == 3:
                        month, day, year = parts
                        return f"{year}{month.zfill(2)}{day.zfill(2)}"
                elif "." in original_date:
                    parts = original_date.split(".")
                    if len(parts) == 3:
                        day, month, year = parts
                        return f"{year}{month.zfill(2)}{day.zfill(2)}"
                elif "-" in original_date and len(original_date.split("-")) == 3:
                    year, month, day = original_date.split("-")
                    return f"{year}{month.zfill(2)}{day.zfill(2)}"
            except:
                pass

    # Fallback to file modification time
    try:
        file_stat = os.stat(image_path)
        mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
        return mod_time.strftime("%Y%m%d")
    except:
        return None
