# Extracts personal names from a body of text.

import spacy

# Load the English language model
nlp = spacy.load("en_core_web_sm")

# Read text from a file
with open("filenames.txt", "r") as file:
    text = file.read()

# Process the text
print("Processing text...")
doc = nlp(text)

# Extract personal names (entities labeled as "PERSON")
personal_names = [entity.text for entity in doc.ents if entity.label_ == "PERSON"]
personal_names = list(set(personal_names))

print("Personal Names Found:", personal_names)
