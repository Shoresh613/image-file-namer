#!/usr/bin/env python3
"""
Example: Advanced usage showing customization options.
"""
from src import ImageFileNamer, BatchProcessor, FilenameBuilder
from src.processors import ContentProcessor, NERProcessor
from src.utils import setup_dependencies


def main():
    print("🔧 Advanced Image File Namer Usage Example")
    print("=" * 50)

    # Setup dependencies
    setup_dependencies()

    # Example 1: Using individual components
    print("\n1️⃣ Using individual components:")

    # Create processors
    content_processor = ContentProcessor()
    ner_processor = NERProcessor()
    filename_builder = FilenameBuilder(max_length=100)  # Custom max length

    # Process a single image step by step
    image_path = "./assets/20230422 United nypost America biden overthrow prompted Hunter false CIA letter States write Flynn campaign Mike signed deputy Morrell.jpg"

    if Path(image_path).exists():
        print(f"Processing: {Path(image_path).name}")

        # Step 1: Extract OCR text
        ocr_text = content_processor.extract_ocr_text(image_path)
        print(f"OCR text length: {len(ocr_text)} characters")

        # Step 2: Get image description
        description = content_processor.get_image_description(image_path)
        print(f"Description: {description[:100]}...")

        # Step 3: Extract named entities
        ner_words = ner_processor.get_words_of_interest(ocr_text)
        print(f"Named entities: {ner_words}")

        # Step 4: Build filename
        filename = filename_builder.build_optimized_filename(
            words_text=f"{ner_words} {description}",
            date_prefix="20230422",
            max_length=100,
        )
        print(f"Generated filename: {filename}")

    # Example 2: Custom batch processor with different settings
    print("\n2️⃣ Custom batch processing:")

    custom_processor = BatchProcessor(rate_limit_per_minute=25)  # Slower processing

    # You could customize the ImageFileNamer here too
    custom_namer = ImageFileNamer(max_filename_length=80)  # Shorter filenames
    custom_processor.image_namer = custom_namer

    print("Custom batch processor created with:")
    print("- Rate limit: 25 images/minute")
    print("- Max filename length: 80 characters")

    # Example 3: Filename builder customization
    print("\n3️⃣ Filename builder customization:")

    builder = FilenameBuilder(max_length=60)

    sample_text = "covid vaccine pandemic trump biden election 2020 fraud investigation"
    sample_date = "20231201"

    filename = builder.build_optimized_filename(
        words_text=sample_text, date_prefix=sample_date, max_length=60
    )

    print(f"Sample text: {sample_text}")
    print(f"With date: {sample_date}")
    print(f"Generated: {filename}")
    print(f"Length: {len(filename)} characters")


if __name__ == "__main__":
    from pathlib import Path

    main()
