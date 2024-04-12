# Path to the text file you want to read
file_path = 'words.txt'

# Create an empty set to store unique words
words_set = set()

# Open the text file in read mode
with open(file_path, 'r', encoding='utf-8') as file:
    # Read each line in the file
    for line in file:
        # Split the line into words based on whitespace
        words = line.split()
        # Add each word to the set
        for word in words:
            # Check if the word contains only alphabetic characters (no numbers)
            if word.isalpha():
                # Add the word to the set, optionally in lowercase to ignore case
                words_set.add(word.lower())  # Remove .lower() if case sensitivity is important

# File path for the output file
output_file_path = 'filtered_words.txt'

# Open the output file in write mode
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    # Write each word from the set to the file, each on a new line
    for word in sorted(words_set):  # Sorting the set for better readability
        output_file.write(word + '\n')

print(f'Words successfully saved to {output_file_path}')
