# from azure.cognitiveservices.vision.computervision import ComputerVisionClient
# from msrest.authentication import CognitiveServicesCredentials
from langdetect import detect
import os
import time
import datetime
from pathlib import Path
from collections import deque

# import yake
import spacy
import re
import subprocess
import sys
import random
from tqdm import tqdm
import ollama
from docling.document_converter import DocumentConverter
import torch

doc_converter = DocumentConverter()


def clean_up_gpu_memory():
    """
    Frees up GPU memory by clearing PyTorch's cache and performing garbage collection.
    """
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        print("GPU memory cleaned up.")
    else:
        print("No GPU available to clean up.")


def download_spacy_model(model_name):
    try:
        # Try to load the spaCy model to check if it's already installed
        import spacy

        spacy.load(model_name)
        print(f"Model {model_name} installed.")
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
            except subprocess.CalledProcessError as e:
                print(f"Failed to download {model_name}: {str(e)}")
        else:
            print("Download cancelled.")
            return 1


# Access environment variables for the Azure Cognitive Services subscription key and endpoint
# Note: These environment variables should be set before running the script
subscription_key = os.getenv("AZURE_IMAGE_KEY")
endpoint = os.getenv("AZURE_IMAGE_ENDPOINT")
names_to_include_file = "./wordlists/names_to_include.txt"  # Create file to use the file, one word on each line
non_personal_names_to_include = "./wordlists/non_personal_names_to_include.txt"  # Create file to use the file, one word on each line
words_to_include_file = "./wordlists/words_to_include.txt"  # Create file to use the file, one word on each line
words_to_remove_file = "./wordlists/words_to_remove.txt"  # Create file to use the file, one word on each line


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename by removing illegal characters and specific words.

    This function takes a filename as input and performs two main sanitization steps:
    1. Replaces any characters that are illegal in file systems with underscores. Illegal characters include
       common filesystem reserved characters as well as additional characters that could cause issues in
       various environments, such as <, >, :, ", /, \, |, ?, *, and various Unicode punctuation characters.
    2. Removes a predefined list of words that are deemed unnecessary or undesirable in filenames. This
       includes common words and phrases in English, Swedish, and some technical terms related to web and
       application development. The removal process respects word boundaries, ensuring only whole words
       are targeted.

    Parameters:
    - filename (str): The original filename to be sanitized.

    Returns:
    - str: The sanitized filename with illegal characters replaced and specified words removed.

    Note:
    The function is designed to reduce the likelihood of filename collisions and to ensure compatibility
    across different file systems and platforms. It does not guarantee uniqueness of the resulting filename
    and does not check against all possible reserved words or symbols in all environments. Additional
    customization of the `illegal_chars` and `words_to_remove` lists may be necessary to meet specific
    requirements.
    """
    illegal_chars = "<>:,.•=-\"/\\|?*βß<>%&\{\}[]()$!#@;^`~'’”“„‚‘´¨»«€£¥—_§±"

    for char in illegal_chars:
        filename = filename.replace(char, "")

    # Remove double words with different capitalizations
    words_seen = set()
    words_in_filename = filename.split()
    new_filename_words = []

    for word in words_in_filename:
        word_lower = word.lower()
        word_singular = word_lower.rstrip(
            "s"
        )  # Simplified checking for plural/singular, "assuming" only simple plurals ending in 's'
        if word_lower not in words_seen and word_singular not in words_seen:
            new_filename_words.append(word)
            # Add both the actual word and its lowercase form to the set
            words_seen.add(word_lower)
            words_seen.add(word_singular)

    # Rebuild the filename from the filtered list of words
    filename = " ".join(new_filename_words)

    # Remove specified words
    words_to_remove = list(load_words_from_file(words_to_remove_file))
    for word in words_to_remove:
        # Using word boundaries (\b) to ensure only whole words are matched
        regex_pattern = r"\s*\b" + re.escape(word) + r"\b\s*"
        filename = re.sub(
            regex_pattern, " ", filename, flags=re.IGNORECASE
        )  # Replace with a single space to avoid concatenation of words

    # Replace multiple spaces with a single space
    filename = re.sub(" +", " ", filename)

    return filename.strip()


def load_words_from_file(file_path):
    input_file_path = file_path
    words_set = {""}

    try:
        with open(input_file_path, "r", encoding="utf-8") as file:
            for line in file:
                word = line.strip()
                words_set.add(word)
    except FileNotFoundError:
        print(f"File '{input_file_path}' not found.")
        return None

    return words_set


def find_dates(text):
    # Pattern to match various date formats
    patterns = [
        r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)",  # YYYY-MM-DD
        r"(?<!\d)(20\d{6})(?!\d)",  # YYYYMMDD
        r"(?<!\d)(20\d{2}-\d{1,2}-\d{1,2})(?!\d)",  # YYYY-M-D or YYYY-MM-D
        r"(?<!\d)(\d{1,2}/\d{1,2}/20\d{2})(?!\d)",  # M/D/YYYY or MM/DD/YYYY
        r"(?<!\d)(\d{1,2}\.\d{1,2}\.20\d{2})(?!\d)",  # D.M.YYYY or DD.MM.YYYY
    ]

    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        matches.extend(found)

    return matches


def extract_date_from_ocr_text(ocr_text):
    """
    Extract the last (most recent or most relevant) date found in OCR text.
    Returns the date in YYYYMMDD format, or None if no date found.
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


def extract_date_from_filename_or_timestamp(image_path):
    """
    Extract date from filename or file timestamp as fallback.
    Returns the date in YYYYMMDD format.
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


def fix_common_ocr_mistakes(text: str):
    text = text.replace("OAnon", "QAnon")
    text = text.replace("Trurnp", "Trump")
    text = text.replace("exarnple", "example")
    text = text.replace("ernptied", "emptied")
    text = text.replace("darnage", "damage")
    text = text.replace("Jirn", "Jim")

    # Remove string of numbers followed by either K or M (for number of likes, views or hours ago)
    text = re.sub(r"\d+[KMh]", "", text)

    # Remove single characters that are not part of a word
    text = re.sub(r"\b\w\b", "", text)

    # Remove more than 1 consecutive space
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Remove string beginning with https or http
    text = re.sub(r"https?://\S+", "", text)

    return text


def get_words_of_interest(text):
    # Specify the categories of interest
    categories = [
        "PERSON",
        "NORP",
        "FAC",
        "ORG",
        "GPE",
        "LOC",
        "PRODUCT",
        "EVENT",
        "WORK_OF_ART",
    ]
    nlp = spacy.load("en_core_web_sm")

    # Process text for NER
    doc = nlp(text)

    # Find words of interest
    words = [ent.text for ent in doc.ents if ent.label_ in categories]

    # People or words we want to include if present
    names = list(load_words_from_file(names_to_include_file)) + list(
        load_words_from_file(non_personal_names_to_include)
    )

    # Add the names to the words list if they are present in the text
    for name in names:
        # Create a regex pattern for the name with word boundaries
        pattern = r"\b" + re.escape(name) + r"\b"

        # Use re.search() to find the pattern in the text
        if re.search(pattern, text):
            words.append(name)

    # Add words from the file if it exists in the text
    words_to_include = load_words_from_file(words_to_include_file)
    lower_case_text = text.lower()

    if words_to_include:
        for word in words_to_include:
            if word in lower_case_text:
                words.append(word)
    words = list(set(words))
    return " ".join(words) + " "


def check_time_in_string(text):
    # search for the pattern "after [number] second" to know for how long to wait
    match = re.search(r"after (\d+) second", text)
    match_days = re.search(r"after (\d+) day", text)

    if match:
        seconds = int(match.group(1))
        return seconds
    elif match_days:
        return -1
    else:
        # If the pattern is not found, return None
        return None


def remove_gibberish(text):
    # Regex pattern for potential OCR gibberish
    # pattern = r"\b(?!\w*'[a-z])([qxzj]{2,}|[bcdfghjklmnpqrstvwxyz]{5,}|[aeiouy]{3,})\b"
    pattern = r"\b(?!\w*'[a-z])(([qxzj]{2,})|([bcdfghjklmnpqrstvwxyz]*[aeiouy]{3,}[bcdfghjklmnpqrstvwxyz]*)|([aeiouy]*[bcdfghjklmnpqrstvwxyz]{5,}[aeiouy]*))\b"

    # Finding matches
    matches = re.findall(pattern, text)
    print("Potential OCR gibberish detected:", matches)

    # Removing gibberish
    cleaned_text = re.sub(pattern, "", text)
    return cleaned_text


def generate_new_filename(image_path, local_llm=True):
    """
    Generates a new filename for an image based on its content, recognized text, and descriptive elements.

    This function uses the Azure Computer Vision API to analyze the content of an image and extract descriptive text and recognized printed text (OCR). It then processes this information to detect the predominant language and extract key phrases from both the descriptive and OCR text. These key phrases are used to generate a new, sanitized filename that reflects the content of the image.

    Parameters:
    - image_path (str): The path to the image file to be analyzed.

    Returns:
    - str: A new, sanitized filename derived from the content and text recognized in the image. The filename is truncated to 135 characters to ensure compatibility with file systems and platforms that have length limitations.

    The function handles language detection failures by defaulting to English ('en'). It also employs keyword extraction to distill the essence of the image's content into a concise, descriptive filename. The resulting filename is sanitized to remove any characters that might be problematic for file systems, including special characters and lengthy word lists.

    Note:
    The function makes external calls to the Azure Computer Vision API and requires a valid endpoint and subscription key. It also uses the 'langdetect' library for language detection and the 'yake' library for keyword extraction. These dependencies need to be installed and configured properly for the function to work.

    Example usage:
    Assuming an image with descriptive content "sunset over the mountains" and recognized text "Enjoy the view",
    the function might generate a filename like "sunset mountains enjoy view".
    """

    if not local_llm:
        client = ComputerVisionClient(
            endpoint, CognitiveServicesCredentials(subscription_key)
        )
    descr_text = ""

    # Description text doesn't produce much useful information in my use case, skipping and can double processing speed and images per month
    # with open(image_path, "rb") as image_stream:
    #     description_results = client.describe_image_in_stream(image_stream)
    #     print("Beskrivning: ", end="")
    #     for caption in description_results.captions:
    #         print("'{}' med säkerhet {:.2f}%".format(caption.text, caption.confidence * 100))
    #         descr_text += caption.text

    # Recognize famous people (only available for microsoft managed accounts)
    # with open(image_path, "rb") as image_stream:
    #     domain_model_results = client.analyze_image_by_domain_in_stream("celebrities", image_stream)
    #     print("\nKända personer i bilden:")
    #     for celebrity in domain_model_results.result["celebrities"]:
    #         print(celebrity["name"])

    # OCR
    ocr_text = ""

    if not local_llm:
        with open(image_path, "rb") as image_stream:
            try:
                ocr_results = client.recognize_printed_text_in_stream(image_stream)
            except Exception as e:
                print(f"OCR failed: {e}")
                seconds = check_time_in_string(str(e))

                if seconds == -1:  # Overused quota, wait for at least a day
                    exit()
                elif seconds is not None:
                    print(
                        f"\nHit limit. Waiting for {seconds} seconds before trying again..."
                    )
                    time.sleep(seconds)
                    with open(image_path, "rb") as image_stream:
                        try:
                            ocr_results = client.recognize_printed_text_in_stream(
                                image_stream
                            )
                        except Exception as e:
                            print(f"OCR failed again: {e}")
                            # This needs to be adapted in case desciptive text or famous people recognition is used
                            fallback_date = extract_date_from_filename_or_timestamp(
                                image_path
                            )
                            return (
                                sanitize_filename(fallback_date).strip()
                                if fallback_date
                                else "unnamed"
                            )
                if "outside the supported" in str(e):
                    print("Image type not supported")
                    fallback_date = extract_date_from_filename_or_timestamp(image_path)
                    return (
                        sanitize_filename(fallback_date).strip()
                        if fallback_date
                        else "unnamed"
                    )

            print("\nText found in image:")
            for region in ocr_results.regions:
                for line in region.lines:
                    line_text = " ".join([word.text for word in line.words])
                    print(line_text)
                    ocr_text += line_text + " "
    else:
        # response = ollama.chat(
        #     model="gemma3",
        #     messages=[
        #         {"role": "user", "content": "Write all text found in the image in natural reading order but in one line, no introduction, no emojis. If text is too small to read efficiently just skip it.", "images": [image_path]}
        #     ],
        # )

        # print(f"OCR text found in image: {response['message']['content']}\n")
        # ocr_text = response["message"]['content']

        print(f"Running Docling OCR on {image_path}...")
        result = doc_converter.convert(str(image_path))
        raw_md = result.document.export_to_markdown()
        ocr_text = re.sub(r"^#+\s*", "", raw_md, flags=re.MULTILINE).strip()
        print(f"OCR text via Docling:\n{ocr_text}\n")

        response = ollama.chat(
            model="gemma3:4b-it-qat",
            messages=[
                {
                    "role": "user",
                    "content": "Output keywords for this image in one line for the purpose of giving the image file a name for easy search. Just a single space between keywords. No emojis.",
                    "images": [image_path],
                }
            ],
        )

        print(f"Description of Image: {response['message']['content']}\n")
        descr_text = response["message"]["content"]

    # Extract date with priority: 1) OCR text, 2) filename, 3) file timestamp
    print("Extracting date with priority: OCR text -> filename -> timestamp")
    found_dates = extract_date_from_ocr_text(ocr_text)
    if found_dates:
        print(f"Date found in OCR text: {found_dates}")
    else:
        print("No date found in OCR text, checking filename and timestamp...")
        found_dates = extract_date_from_filename_or_timestamp(image_path)
        if found_dates:
            print(f"Date found in filename/timestamp: {found_dates}")
        else:
            print("No date found in filename or timestamp")

        # try:
        #     # Detect the language
        #     ocr_lang = detect(ocr_text)
        #     print(f"The detected language of the OCR text is: {ocr_lang}")
        # except Exception as e:
        #     print(f"Language detection failed: {e}")
        #     ocr_lang = "en"

        # try:
        #     # Detect the language
        #     desc_lang = detect(descr_text)
        #     print(f"The detected language of the descritive text is: {desc_lang}")
        # except Exception as e:
        #     print(f"Language detection failed: {e}")
        #     desc_lang = "en"

        # max_ngram_size = 2
        # deduplication_threshold = 0.4
        # numOfKeywords = 15

        # # Extract keywords from the OCR text
        # language = "sv" if ocr_lang == "sv" else "en"

        # kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
        # keywords = kw_extractor.extract_keywords(sanitize_filename(ocr_text))

        # ocr_kw = ""
        # for kw in keywords:
        #     ocr_kw += kw[0] + " "

        response = ollama.chat(
            model="gemma3:4b-it-qat",
            messages=[
                {
                    "role": "user",
                    "content": "Out of the following words, pick 15 keywords that you think are most relevant for naming an image file. If you can't find 15, just pick the ones you think are most relevant. No other text in the reply, no motivations, just the keywords one after another in a single line with a single space between: "
                    + ocr_text
                    + " "
                    + descr_text,
                }
            ],
        )
    ocr_kw = response["message"]["content"]
    print(f"OCR and description keywords: {ocr_kw}\n")

    # Add back any words of people, places, organizations etc to the OCR keywords
    words = get_words_of_interest(ocr_text)
    print(f"Words of interest: {words}")
    ocr_kw = words + ocr_kw

    # # Extract keywords from the description text
    # language = "sv" if ocr_lang == "sv" else "en"
    # kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
    # keywords = kw_extractor.extract_keywords(descr_text)

    # descr_kw = ""
    # for kw in keywords:
    #     descr_kw += kw[0] + " "

    # print(f"Description keywords: {descr_kw}")

    new_file_name = ocr_kw if ocr_kw != "" else f"unnamed{random.randint(0, 1000)}"
    # new_file_name = descr_kw + ocr_kw if ocr_kw != "" else descr_kw.strip()

    new_file_name = sanitize_filename(
        fix_common_ocr_mistakes(remove_gibberish(new_file_name))
    )
    new_file_name = " ".join((set(new_file_name.split())))

    if found_dates:
        new_file_name = found_dates + " " + new_file_name.strip()

    response = ollama.chat(
        model="gemma3:4b-it-qat",
        messages=[
            {
                "role": "user",
                "content": "If there are repeats of words or names in this text, only keep one of those words or names. Examples: If 'FBI/DOJ fbi DOJ' in the string, keep only 'FBI DOJ', if 'WhiteHouse White House' keep only 'White House', if 'vaccine vaccin' keep only 'vaccine', if 'DaveWeldon Dave Weldon' keep only 'Dave Weldon'. No other text in the reply, no motivations, just the keywords one after another in a single line with a single space between: "
                + new_file_name,
            }
        ],
    )
    new_file_name = response["message"]["content"]
    # truncate the text to 135 characters for filename compatibility (Android file transfer?)
    new_file_name = new_file_name[:135].strip()

    return new_file_name


def count_image_files(directory):
    files = os.listdir(directory)
    image_files = [
        file
        for file in files
        if file.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp")
        )
    ]

    return len(image_files)


def process_images(source_folder, target_folder, rate_limit_per_minute=9):
    """
    Processes and renames image files from a source folder to a target folder with rate limiting.

    This function iterates over all files in the specified source folder, processes each image file by generating a new filename based on its content, and moves it to the target folder. To avoid overloading resources or API limits, it implements a rate limit for processing images, defined by the number of images processed per minute.

    Parameters:
    - source_folder (str): The path to the source folder containing the images to be processed.
    - target_folder (str): The path to the target folder where processed images will be moved.
    - rate_limit_per_minute (int, optional): The maximum number of images to process per minute. Default is 9, so as not to exceed the 20 calls per minute limit.

    Behavior:
    - The function first ensures that the target folder exists, creating it if necessary.
    - It employs a deque to track the processing timestamps of each image, ensuring that the rate of processing does not exceed the specified limit.
    - If the rate limit is reached, the function will pause processing until it is safe to continue, based on the timestamps in the deque.
    - Each image is processed by generating a new filename. This operation can involve analyzing the image content, recognizing text, or other custom processing logic encapsulated in the `generate_new_filename` function.
    - The image is then moved to the target folder with its new name. If an error occurs during this operation (e.g., a filename collision), the function attempts to move the file with an altered name. If this second attempt fails, the image is skipped.
    - Processing information, including rate limiting actions, is printed to the console for monitoring.

    Notes:
    - This function does not handle nested directories within the source folder; it processes files directly contained in the specified path.
    - This function does not rate limit to keep it under the 5 000 API calls per month limit.

    Example usage:
    To process images from a folder named 'input_images' to 'processed_images' with a limit of 5 images per minute:
    process_images('input_images', 'processed_images', rate_limit_per_minute=5)
    """

    # Ensure target folder exists
    Path(target_folder).mkdir(parents=True, exist_ok=True)

    # Use a deque to track the timestamps of processed images
    timestamps = deque()

    # Calculate total number of files once
    total_files = count_image_files(source_folder)
    processed_files = 0
    for image in tqdm(
        Path(source_folder).glob("*"),
        total=total_files,
        desc="Processing images",
        unit="image",
    ):
        # Process only image files
        if image.is_file() and image.suffix.lower() in [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tiff",
            ".webp",
        ]:
            current_time = time.time()
            print(f"Processing {image} ({processed_files +1} of {total_files})")

            # Remove timestamps older than 61 seconds from the deque (+1 to be on the safe side)
            while timestamps and current_time - timestamps[0] > 61:
                timestamps.popleft()

            # Check if processing limit has been reached
            if len(timestamps) >= rate_limit_per_minute:
                sleep_time = 61 - (current_time - timestamps[0])
                print(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                # After sleeping, update current time
                current_time = time.time()

            # Proceed with processing
            new_filename = generate_new_filename(image).strip() + image.suffix
            new_path = Path(target_folder) / new_filename

            # Example operation: Rename (move) file to new location with a new name
            try:
                os.rename(image, new_path)
            except Exception as e:
                new_filename = generate_new_filename(image).strip() + "_" + image.suffix
                new_path = Path(target_folder) / new_filename
                try:  # Try again with a different name
                    os.rename(image, new_path)
                except Exception as e:
                    print(f"Failed to process {image}: {e}")
                    continue

            # Log the timestamp of this processing
            timestamps.append(time.time())

            print(f"Processed: {new_path}")
            processed_files += 1
    print(f"Finished processing {processed_files} images.")


def main():
    # Specify your source and target folders. Could be the Screenshot folder directly if you're brave.
    source_folder = "./images/to_name"
    target_folder = "./images/named_images"
    # Processing maximum of 10 images per minute as 2 calls and 20 max per minute, 9 to be safe
    # But if not using the description text, can process 18 images per minute, or 17 to be on the safe side
    # Seems it doesn't only count per minute, so finetuning to quarter of a minute instead, to avoid Exceptions.

    # Check if the variables were found
    # if subscription_key and endpoint:
    #     print("Found the environment variables.")
    # else:
    #     print("Azure Environment variables not found.")
    #     return 1

    # Check if spacy language model is downloaded, ask to download if not
    # Replace 'en_core_web_sm' with your specific spaCy model name
    code = download_spacy_model("en_core_web_sm")
    if code == -1:
        print("Please install language model for spaCy. Exiting.")

    clean_up_gpu_memory()
    process_images(source_folder, target_folder, 100)


if __name__ == "__main__":
    main()
