import os
from pathlib import Path
import re

def sanitize_filename(filename: str):
    illegal_chars = '<>:."/\\|?*βß<>%&\{\}[]()$!#@;^`~\'’”“„‚‘´¨'
    words_to_remove = ['text', 'graphical', 'and', 'or', 'in', 'as', 'of', 'is', 'so', 'the', 'prenumerera', 'vid', 'på', 'i', 'och', 'eller',
                        'ägg', 'Återpublicera', 'ditt', 'Gillamarkeringar', 'Visningar', 'application', 'Översätt', 'upp', 'till', 'en', 'ett',
                         'inlägget', 'två', 'tre', 'on', 'trending', 'som', 'that', 'this', 'with', 'for', 'from', 'your', 'you', 'are', 'have',
                         'at', 'bit.ly', 'Återpubliceringar', 'Bokmärken', 'bitIy', 'website', 'screenshot', 'user', 'interface']
    for char in illegal_chars:
        filename = filename.replace(char, '')

    # Remove specified words
    for word in words_to_remove:
        # Using word boundaries (\b) to ensure only whole words are matched
        regex_pattern = r'\b' + re.escape(word) + r'\b'
        filename = re.sub(regex_pattern, '', filename, flags=re.IGNORECASE).strip()
    
    # Remove linebreaks, carriage returns, and any other non-printable or hidden characters
    filename = re.sub(r'[\r\n\t]+', '', filename)  # Remove common whitespace characters not suitable for filenames
    filename = re.sub(r'[\x00-\x1F\x7F-\x9F]+', '', filename)  # Remove non-printable characters and control characters

    return filename

def shorten_filenames(directory):
    # Ensure the directory exists
    if not os.path.exists(directory):
        print(f"The directory {directory} does not exist.")
        return
    
    counter = 0
    for file in Path(directory).iterdir():
        if file.is_file():
            print(f"Processing: {file.name}, Length: {len(file.name)}")  # Debug print
            filename, file_extension = os.path.splitext(file.name)
            sanitized_filename = sanitize_filename(filename)
            if sanitized_filename == filename:
                print("No need to sanitize.")
            else:      
                counter += 1
                shortened_filename = sanitized_filename + file_extension
                new_file_path = file.with_name(shortened_filename)
                
                try:
                    file.rename(new_file_path)
                except FileExistsError:
                    print(f"File '{shortened_filename}' already exists. Adding '_2'.")
                    try:
                        shortened_filename = sanitized_filename +"_2"+ file_extension
                        new_file_path = file.with_name(shortened_filename)
                        file.rename(new_file_path)
                    except FileExistsError:
                        print(f"File '{shortened_filename}' also already exists. Skipping")

                print(f"Renamed '{file.name}' to '{shortened_filename}'")

    print(f"Renamed {counter} files in total.")

# Example usage
directory_path = './images/named_images/'
shorten_filenames(directory_path)
