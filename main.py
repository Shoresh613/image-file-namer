#!/usr/bin/env python3
"""
Main entry point for the Image File Namer application.

This script provides a clean interface to the modularized image file naming system.
"""
import argparse
from pathlib import Path

from src import BatchProcessor
from src.config import (
    DEFAULT_SOURCE_FOLDER,
    DEFAULT_TARGET_FOLDER,
    DEFAULT_RATE_LIMIT_PER_MINUTE,
)
from src.utils import clean_up_gpu_memory, setup_dependencies


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Intelligent image file naming using OCR, LLM, and NER"
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default=DEFAULT_SOURCE_FOLDER,
        help=f"Source folder containing images to rename (default: {DEFAULT_SOURCE_FOLDER})",
    )
    parser.add_argument(
        "--target",
        "-t",
        type=str,
        default=DEFAULT_TARGET_FOLDER,
        help=f"Target folder for renamed images (default: {DEFAULT_TARGET_FOLDER})",
    )
    parser.add_argument(
        "--rate-limit",
        "-r",
        type=int,
        default=DEFAULT_RATE_LIMIT_PER_MINUTE,
        help=f"Maximum images to process per minute (default: {DEFAULT_RATE_LIMIT_PER_MINUTE})",
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip dependency setup (use if already configured)",
    )

    args = parser.parse_args()

    print("🖼️  Image File Namer - Intelligent Image Renaming System")
    print("=" * 60)

    # Setup dependencies unless skipped
    if not args.skip_setup:
        if not setup_dependencies():
            print("❌ Dependency setup failed. Exiting.")
            return 1

    # Validate paths
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ Source folder '{args.source}' does not exist.")
        return 1

    target_path = Path(args.target)

    print(f"📁 Source folder: {source_path}")
    print(f"📁 Target folder: {target_path}")
    print(f"⚡ Rate limit: {args.rate_limit} images/minute")
    print("-" * 60)

    # Clean up GPU memory before starting
    clean_up_gpu_memory()

    # Create batch processor and run
    processor = BatchProcessor(rate_limit_per_minute=args.rate_limit)

    try:
        processor.process_images(source_path, target_path)
        print("✅ Processing completed successfully!")
        return 0
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user.")
        return 1
    except Exception as e:
        print(f"❌ Processing failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
