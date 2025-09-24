"""
Setup utilities for the Image File Namer application.
"""

import subprocess
import sys
from typing import Optional

import spacy


def download_spacy_model(model_name: str) -> Optional[int]:
    """
    Download and install a spaCy model if it's not already available.

    Args:
        model_name: Name of the spaCy model to download

    Returns:
        0 on success, 1 on failure, None if user cancels
    """
    try:
        # Try to load the spaCy model to check if it's already installed
        spacy.load(model_name)
        print(f"Model {model_name} is already installed.")
        return 0
    except OSError:
        # If model is not installed, ask the user for permission to download
        response = input(
            f"Model {model_name} not found. Do you want to download it? (yes/no): "
        )
        if response.lower() == "yes":
            try:
                # Run the download command
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model_name], check=True
                )
                print(f"Model {model_name} downloaded successfully.")
                return 0
            except subprocess.CalledProcessError as e:
                print(f"Failed to download {model_name}: {str(e)}")
                return 1
        else:
            print("Download cancelled.")
            return None


def setup_dependencies():
    """
    Set up all required dependencies for the application.

    Returns:
        True if setup successful, False otherwise
    """
    from ..config import SPACY_MODEL

    print("Setting up dependencies for Image File Namer...")

    # Download spaCy model
    result = download_spacy_model(SPACY_MODEL)
    if result == 1:
        print("Failed to set up spaCy model. Please install it manually:")
        print(f"python -m spacy download {SPACY_MODEL}")
        return False
    elif result is None:
        print("Setup cancelled by user.")
        return False

    print("All dependencies set up successfully!")
    return True
