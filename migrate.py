#!/usr/bin/env python3
"""
Migration script to demonstrate the transition from old to new modular structure.

This script shows how the old monolithic functions map to the new modular classes.
"""


def demonstrate_migration():
    """Show how to migrate from old to new structure."""

    print("🔄 Image File Namer - Migration Guide")
    print("=" * 50)

    # Show old vs new imports
    print("\n📦 Import Changes:")
    print("OLD:")
    print("  from image_file_namer import generate_new_filename, process_images")
    print("\nNEW:")
    print("  from src import ImageFileNamer, BatchProcessor")
    print("  # OR use the simple API:")
    print("  from api import ImageFileNamerAPI")

    # Show function mapping
    print("\n🔧 Function Mapping:")

    print("\n1. Single Image Processing:")
    print("   OLD: filename = generate_new_filename('image.jpg')")
    print("   NEW: namer = ImageFileNamer()")
    print("        filename = namer.generate_new_filename('image.jpg')")
    print("   API: api = ImageFileNamerAPI()")
    print("        filename = api.rename_single_image('image.jpg')")

    print("\n2. Batch Processing:")
    print("   OLD: process_images(source_folder, target_folder, rate_limit)")
    print("   NEW: processor = BatchProcessor(rate_limit)")
    print("        processor.process_images(source_folder, target_folder)")
    print("   API: api = ImageFileNamerAPI()")
    print("        api.process_folder(source_folder, target_folder, rate_limit)")

    print("\n3. Utility Functions:")
    print("   OLD: from image_file_namer import sanitize_filename, find_dates")
    print("   NEW: from src.utils import sanitize_filename_basic, find_dates")
    print("        from src.core import FilenameBuilder")
    print("        builder = FilenameBuilder()")
    print("        clean_name = builder.sanitize_filename(filename)")

    # Show benefits
    print("\n✨ Benefits of New Structure:")
    benefits = [
        "Modular components that can be used independently",
        "Better type hints and IDE support",
        "Easier testing of individual components",
        "Centralized configuration management",
        "Clear separation of concerns",
        "Easy to extend with new features",
        "Backward compatible with legacy code",
    ]

    for i, benefit in enumerate(benefits, 1):
        print(f"   {i}. {benefit}")

    print("\n🏃‍♂️ Quick Migration Steps:")
    steps = [
        "Keep using image_file_namer.py for existing scripts (still works!)",
        "For new code, use the modular structure via main.py or api.py",
        "Gradually migrate existing code using the mapping above",
        "Take advantage of new features like customizable components",
    ]

    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")

    print(f"\n📚 See MODULAR_README.md for complete documentation")
    print(f"📁 Check examples/ folder for usage examples")
    print(f"🧪 Test the new structure with: python3 main.py --help")


if __name__ == "__main__":
    demonstrate_migration()
