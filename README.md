# image-file-namer

Simple script that uses Azure AI Vision (to get a textual description) and a local NLP library (to extract keywords) to rename image files, giving them descriptive filenames.
Example use cases are screenshots or downloaded images, to be able to find them based on a textual search on the filename.

It requires an API key and path at Microsoft Azure that you need to set as environment variables (see below). 
Naturally, there is a cost involved for using the API, unless you happen to be a student, in which case you get 5000 such API calls for free each months. 

The script makes sure it doesn't exceed the limit of 20 API calls per minute (1-3 calls for every image, default is 1 call, which leads to a processing speed of 4-18 images per minute to be on the safe side). It does not keep track of exceeding 5000 per month, but if more calls are made, they will simply be refused unless you pay for more.

There are some tweaks to be made to get the best results for your situation, which include creating the following files in a `wordlist` folder in the root of this directory, where words to keep or remove from the filenames are specified:

* `names_to_include.txt`: Names to always include in the filename if detected (case sensitive) 
* `words_to_include.txt`: Words to always include in the filename if detected (case insensitive)
* `words_to_remove.txt`: Words never to include in the filename (case insensitive)

If these files are nonexistent, you might not get all the words you want, and you might see words you don't want. It is possible to create the files by extracting personal names using `words_to_set.py` for instance, and adapting it for the other files.

**Example:**
Image resized using `resize_images.py`and file size cut to less than 10% of the original file size. Then run through `image_file_namer.py`to generate the filename. 

![Example Image](assets/20230422%20United%20nypost%20America%20biden%20overthrow%20prompted%20Hunter%20false%20CIA%20letter%20States%20write%20Flynn%20campaign%20Mike%20signed%20deputy%20Morrell.jpg "Example image")

Generated filename: `"20230422 United nypost America biden overthrow prompted Hunter false CIA letter States write Flynn campaign Mike signed deputy Morrell.jpg"`

The date is generated from the filename. Edit the script to suit your preferred date format.

### Folders
All relative to the git directory:

Sure, let's extend the markdown table to include descriptions for all the folders shown in the screenshot.

### Folders
All relative to the git directory:

| Folder Path                      | Description                                                 |
|----------------------------------|-------------------------------------------------------------|
| `./images/named_images`          | Named images are stored here                                |
| `./images/cropped`               | Contains images that have been cropped                      |
| `./images/resized`               | Contains images that have been resized after processing     |
| `./images/scale_horizontally`    | Images to be scaled in the horizontal dimension             |
| `./images/scaled_horizontally`   | Contains horizontally scaled images after processing        |
| `./images/to_crop`               | Images to be cropped are placed here                        |
| `./images/to_name`               | Images that are ready to be renamed are stored here         |

### Environment variables
| Variable               | Description                                        |
|------------------------|----------------------------------------------------|
| `AZURE_IMAGE_ENDPOINT` | Endpoint URL for the Azure Image service           |
| `AZURE_IMAGE_KEY`      | Authentication key for accessing the Azure Image service |

###
Required step to ensure filter out keywords in English (change to your use case, also in the code):
`python -m spacy download en_core_web_sm`

### Still to do
* Improved understanding of the images would be nice. But that would mean training a model.
* Removing gibberish generated by OCR 

### Extra related scripts developed in the process

#### Image preprocessing
`resize_images.py`: Resizes images 50% and stores as jpeg (70% quality), suitable for downscaling screenshots for storage.

`scale_hor_50.py`: Resizes images horizontally in `scale_horizontally` folder, saves in `scaled_horizontally` folder. There are some presets that can be extended based on your use cases.

`crop.py`: Crops images based on presets defined in `cropping_modes.json`, see `sample_cropping_modes.json` for example and adapt to your use case. 

#### NLP and file preparations
`clean_file_name.py`: Removes illegal charachters from the filename, and shortens it to enable transfer to Android (135 char limit? At least for me when transferring from Windows).

`name_extractor.py`: Extracts personal names from a body of text.

`words_to_set.py`: Reads a text file consisting of words you want to keep in the description, filters out words with numbers in them, removes duplicates, sorts the words and outputs a file with every words on a line of its own. Can be used to generate the word list files used by the main script, e.g. `words_to_include.txt` etc.

### Changelog
v. 0.1.16: Version numbering introduced.