# image-file-namer

Simple script that uses Azure AI Vision (to get a textual description) and a local NLP library (to extract keywords) to rename image files, giving them descriptive filenames.
Example use cases are screenshots or downloaded images, to be able to find them based on a textual search on the filename.

It requires an API key and path at MicroSoft Azure that you need to set as environment variables (see below). 
Naturally, there is a cost involved for using the API, unless you happen to be a student, in which case you get 5000 such API calls for free each months. 

The script makes sure it doesn't exceed the limit of 20 API calls per minute (2 calls for every image which leads to a processing speed of 9 images per minute to be on the safe side). It does not keep track of exceeding 5000 per month, but if more calls are made, they will simply be refused unless you pay for more.

Words to remove from the filenames are based on English and Swedish, but can easily be updated.

**Example:**

![Example Image](assets/States%20CIA%20United%20LTG%20America%20Morrell%20director%20Mike%20deputy%2020230422%20nypos%20Flynn.jpg "Example image")

Generated filename: `"20230422 LTG States participants Morrell campaign CIA apr write Flynn Biden America Hunter false signed deputy Mike letter United promp.jpg"`

### Folders
All relative to the git directory:

| Folder Path             | Description                            |
|-------------------------|----------------------------------------|
| `./images/`             | Place images here to automatically get them renamed |
| `./images/named_images` | Named images are stored here           |

### Environment variables
| Variable               | Description                                        |
|------------------------|----------------------------------------------------|
| `AZURE_IMAGE_ENDPOINT` | Endpoint URL for the Azure Image service           |
| `AZURE_IMAGE_KEY`      | Authentication key for accessing the Azure Image service |

###
Required step to ensure personal names are kept as keywords:
`python -m spacy download en_core_web_sm`

### Still to do
Improved understanding of the images would be nice. Also a better keyword extraction. As seen in the example, 'Hunter' is turned into 'Hun', also nypost would be nice to have included. 

### Extra related scripts developed in the process

`clean_file_name.py`: Removes illegal charachters from the filename, and shortens it to enable transfer to Android (135 char limit? At least for me when transferring from Windows).

`name_extractor.py`: Extracts personal names from a body of text.

`resize_images.py`: Resizes images 50% and stores as jpeg (70% quality), suitable for downscaling screenshots for storage.

`words_to_set.py`: Reads a text file consisting of words you want to keep in the description, filters out words with numbers in them, removes duplicates, sorts the words and outputs a file with every words on a line of its own. Can be used to generate `filtered_words.txt` used by the main script.