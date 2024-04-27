import os

def load_words_to_remove(filepath):
    try:
        with open(filepath, 'r') as file:
            words_to_remove = [line.strip().lower() for line in file]
    except Exception as e:
        print(f"Error reading file: {filepath}. Error: {e}")
        words_to_remove = []
    return words_to_remove

def remove_words_from_filenames(folder_path, words_to_remove):
    for filename in os.listdir(folder_path):
        original_filename = filename
        name, extension = os.path.splitext(filename)
        # Split the name by spaces and reconstruct without words to remove, preserving case
        new_name_parts = []
        for word in name.split():
            # Remove the word if it matches any in the list, case-insensitive
            if word.lower() not in words_to_remove:
                new_name_parts.append(word)
        new_name = ' '.join(new_name_parts) + extension
        if new_name != original_filename:
            try:
                os.rename(os.path.join(folder_path, original_filename), os.path.join(folder_path, new_name))
                print(f"Renamed '{original_filename}' to '{new_name}'")
            except Exception as e:
                print(f"Failed to rename '{original_filename}' to '{new_name}'. Error: {e}")

def main():
    words_filepath = 'wordlists/words_to_remove.txt'
    folder_path = 'named_files'  # Adjust the folder path if necessary
    words_to_remove = load_words_to_remove(words_filepath)
    if words_to_remove:
        remove_words_from_filenames(folder_path, words_to_remove)
    else:
        print("No words to remove due to missing file. Exiting...")

if __name__ == "__main__":
    main()
