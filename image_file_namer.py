from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from langdetect import detect
import os
import time
from pathlib import Path
from collections import deque
import yake
import spacy
import re


# Access environment variables for the Azure Cognitive Services subscription key and endpoint
# Note: These environment variables should be set before running the script
subscription_key = os.getenv('AZURE_IMAGE_KEY')
endpoint = os.getenv('AZURE_IMAGE_ENDPOINT')
names_to_include_file = './wordlists/names_to_include.txt' # Create file to use the file, one word on each line
words_to_include_file = './wordlists/words_to_include.txt' # Create file to use the file, one word on each line
words_to_remove_file = './wordlists/words_to_remove.txt' # Create file to use the file, one word on each line

# Check if the variables were found
if subscription_key and endpoint:
    print("Found the environment variables.")
else:
    print("Environment variables not found.")

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
    illegal_chars = '<>:,.•=-"/\\|?*βß<>%&\{\}[]()$!#@;^`~\'’”“„‚‘´¨'
    
    for char in illegal_chars:
        filename = filename.replace(char, '')

    # Remove specified words
    words_to_remove = list(load_words_from_file(words_to_remove_file))
    for word in words_to_remove:
        # Using word boundaries (\b) to ensure only whole words are matched
        regex_pattern = r'\s*\b' + re.escape(word) + r'\b\s*'
        filename = re.sub(regex_pattern, ' ', filename, flags=re.IGNORECASE)  # Replace with a single space to avoid concatenation of words

    return filename

def load_words_from_file(file_path):
    input_file_path = file_path
    words_set = {''}

    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                word = line.strip()
                words_set.add(word)
    except FileNotFoundError:
        print(f"File '{input_file_path}' not found.")
        return None
    
    return words_set

def find_dates(text):
    # Pattern to match YYYYMMDD or YYYY-MM-DD, ensuring no digits before or after
    pattern = r'(?<!\d)(20\d{2}-\d{2}-\d{2}|20\d{6})(?!\d)'
    matches = re.findall(pattern, text)
    
    return matches

def fix_common_ocr_mistakes(text:str):
    text = text.replace('OAnon', 'QAnon')
    text = text.replace('Trurnp', 'Trump')

    # Use regex to remove string of numbers followed by either K or M (for number of likes or views)
    text = re.sub(r'\d+[KM]', '', text)

    # Remove single characters that are not part of a word
    text = re.sub(r'\b\w\b', '', text)

    # Remove more than 1 consecutive space
    text = re.sub(r'\s{2,}', ' ', text).strip()
     

    return text

def get_words_of_interest(text):
    # Specify the categories of interest
    categories = ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART']
    nlp = spacy.load("en_core_web_sm")

    # Process text for NER
    doc = nlp(text)

    # Find words of interest
    words = [ent.text for ent in doc.ents if ent.label_ in categories]
    
    # People or words we want to include if present
    names = list(load_words_from_file(names_to_include_file))
    
    # Add the names to the words list if they are present in the text
    for name in names:
        # Create a regex pattern for the name with word boundaries
        pattern = r'\b' + re.escape(name) + r'\b'
        
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

def generate_new_filename(image_path):
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

    client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
    descr_text=""

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
    with open(image_path, "rb") as image_stream:
        ocr_results = client.recognize_printed_text_in_stream(image_stream)
        print("\nText funnen i bilden:")
        for region in ocr_results.regions:
            for line in region.lines:
                line_text = " ".join([word.text for word in line.words])
                print(line_text)
                ocr_text += line_text + " "
    try:
        # Detect the language
        ocr_lang = detect(ocr_text)
        print(f"The detected language of the OCR text is: {ocr_lang}")
    except Exception as e:
        print(f"Language detection failed: {e}")
        ocr_lang = "en"

    try:
        # Detect the language
        desc_lang = detect(descr_text)
        print(f"The detected language of the descritive text is: {desc_lang}")
    except Exception as e:
        print(f"Language detection failed: {e}")
        desc_lang = "en"

    max_ngram_size = 2
    deduplication_threshold = 0.4
    numOfKeywords = 15

    # Extract keywords from the OCR text
    language = "sv" if ocr_lang == "sv" else "en"
        
    kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
    keywords = kw_extractor.extract_keywords(sanitize_filename(ocr_text))

    ocr_kw = ""
    for kw in keywords:
        ocr_kw += kw[0] + " "

    print(f"OCR keywords: {ocr_kw}")
    
    # Add back any words of people, places, organizations etc to the OCR keywords
    words = get_words_of_interest(ocr_text)
    print(f"Words of interest: {words}")
    ocr_kw = words + ocr_kw 

    # Extract keywords from the description text
    language = "sv" if ocr_lang == "sv" else "en"
    kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
    keywords = kw_extractor.extract_keywords(descr_text)

    descr_kw = ""
    for kw in keywords:
        descr_kw += kw[0] + " "

    print(f"Description keywords: {descr_kw}")

    # If there's a date in the image path (including it's file name), use that
    new_file_name = descr_kw + ocr_kw if ocr_kw != "" else descr_kw.strip()
    found_dates = str(find_dates(str(image_path))).replace('-','')


    new_file_name = sanitize_filename(fix_common_ocr_mistakes(new_file_name))
    new_file_name = " ".join((set(new_file_name.split())))

    if found_dates:
        new_file_name = sanitize_filename(found_dates).strip() + " " + new_file_name.strip()
    # truncate the text to 135 characters for filename compatibility (Android file transfer?)
    new_file_name = new_file_name[:135].strip()

    return new_file_name

def count_image_files(directory):
    files = os.listdir(directory)
    image_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'))]
    
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
    for i, image in enumerate(Path(source_folder).glob('*'), start=0):
        # Process only image files
        if image.is_file() and image.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
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
            new_filename = generate_new_filename(image) + image.suffix
            new_path = Path(target_folder) / new_filename
            
            # Example operation: Rename (move) file to new location with a new name
            try:
                os.rename(image, new_path)
            except Exception as e:
                new_filename = generate_new_filename(image).strip() + "_" + image.suffix
                new_path = Path(target_folder) / new_filename
                try: # Try again with a different name
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
    # Specify your source and target folders
    source_folder = './images'
    target_folder = './images/named_images'
    # Processing maximum of 10 images per minute as 2 calls and 20 max per minute, 9 to be safe
    # But if not using the description text, can process 18 images per minute, or 17 to be on the safe side
    process_images(source_folder, target_folder, 17)

if __name__ == "__main__":
    main()