# Image File Namer - Modular Architecture

## 🏗️ Project Structure

The Image File Namer has been completely modularized into a clean, maintainable architecture:

```
src/
├── __init__.py                 # Main package exports
├── config/                     # Configuration settings
│   ├── __init__.py
│   └── settings.py            # All configuration constants
├── core/                      # Main business logic
│   ├── __init__.py
│   ├── batch_processor.py     # Batch image processing
│   ├── filename_builder.py    # Filename generation & optimization
│   └── image_file_namer.py    # Main orchestration class
├── processors/                # Specialized processors
│   ├── __init__.py
│   ├── content_processor.py   # OCR & LLM content analysis
│   └── ner_processor.py       # Named Entity Recognition
└── utils/                     # Utility functions
    ├── __init__.py
    ├── date_utils.py          # Date extraction utilities
    ├── file_utils.py          # File operations & basic text utils
    ├── setup.py               # Dependency setup utilities
    └── text_utils.py          # Text processing & OCR corrections
```

## 🚀 Quick Start

### Using the Command Line Interface

```bash
# Basic usage - process images with default settings
python main.py

# Custom source and target folders
python main.py --source ./my_images --target ./renamed_images

# With custom rate limiting
python main.py --source ./images --target ./output --rate-limit 50

# Skip dependency setup (if already configured)
python main.py --skip-setup
```

### Using the Simple API

```python
from api import ImageFileNamerAPI

# Initialize API
api = ImageFileNamerAPI()

# Rename a single image
new_name = api.rename_single_image("path/to/image.jpg")

# Process a folder
api.process_folder("./source_images", "./renamed_images")
```

### Using Individual Components

```python
from src import ImageFileNamer, BatchProcessor
from src.core import FilenameBuilder
from src.processors import ContentProcessor, NERProcessor

# Create custom filename builder
builder = FilenameBuilder(max_length=100)

# Create custom image namer
namer = ImageFileNamer(max_filename_length=120)

# Process single image
filename = namer.generate_new_filename("image.jpg")
```

## 📁 Key Components

### Core Classes

#### `ImageFileNamer`
Main orchestration class that coordinates all processing steps:
- OCR text extraction via Docling
- Image description via LLM
- Date detection with fallback hierarchy
- Named entity recognition via spaCy
- Optimized filename generation

#### `BatchProcessor`  
Handles bulk image processing with:
- Rate limiting
- Progress tracking
- Error handling and recovery
- File conflict resolution

#### `FilenameBuilder`
Advanced filename generation with:
- Word deduplication
- Length optimization
- Wordlist filtering
- Illegal character removal

### Processors

#### `ContentProcessor`
- OCR text extraction using Docling
- Image description via Ollama LLM
- Keyword extraction and selection

#### `NERProcessor`
- Named Entity Recognition using spaCy
- Custom word list integration
- Entity category filtering

### Utilities

#### Date Processing
- Multiple date format detection
- OCR text date extraction
- Filename date parsing  
- File timestamp fallback

#### Text Processing
- OCR error correction
- Gibberish removal
- Word deduplication
- Text sanitization

## 🔧 Configuration

All configuration is centralized in `src/config/settings.py`:

```python
# Customize processing settings
DEFAULT_MAX_FILENAME_LENGTH = 135
DEFAULT_RATE_LIMIT_PER_MINUTE = 100

# Modify LLM models
OLLAMA_MODEL_DESCRIPTION = "gemma3:4b-it-qat" 
OLLAMA_MODEL_KEYWORDS = "gemma3:4b-it-qat"

# Adjust NER categories
NER_CATEGORIES = ["PERSON", "ORG", "GPE", "LOC", ...]
```

## 📚 Examples

See the `examples/` directory for detailed usage examples:

- `basic_usage.py` - Simple API usage
- `advanced_usage.py` - Custom component configuration

## 🔀 Migration from Old Code

The modular structure maintains full backward compatibility. Key changes:

### Old Usage:
```python
# Old monolithic approach
from image_file_namer import generate_new_filename, process_images
filename = generate_new_filename("image.jpg")
process_images(source, target)
```

### New Usage:
```python
# New modular approach
from src import ImageFileNamer, BatchProcessor
namer = ImageFileNamer()
filename = namer.generate_new_filename("image.jpg")

processor = BatchProcessor()
processor.process_images(source, target)
```

## 🧪 Testing

Each module can be tested independently:

```python
# Test individual components
from src.processors import ContentProcessor
processor = ContentProcessor()
ocr_text = processor.extract_ocr_text("test_image.jpg")

# Test utilities
from src.utils import extract_date_from_ocr_text
date = extract_date_from_ocr_text("Meeting on 2023-12-25")
```

## 🎯 Benefits of Modular Architecture

1. **Maintainability**: Each component has a single responsibility
2. **Testability**: Individual modules can be tested in isolation  
3. **Extensibility**: Easy to add new processors or modify existing ones
4. **Reusability**: Components can be used independently in other projects
5. **Configuration**: Centralized settings management
6. **Type Safety**: Better type hints and IDE support

## 🔮 Future Extensions

The modular architecture makes it easy to add:

- New OCR engines (replace `ContentProcessor`)
- Different LLM backends (modify `ContentProcessor`)
- Additional NER models (extend `NERProcessor`)
- Custom filename strategies (extend `FilenameBuilder`)
- New output formats (extend `BatchProcessor`)
