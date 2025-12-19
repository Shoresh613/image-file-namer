# image-file-namer

Used to give image files descriptive filenames. Included is also a collection of scripts to prepare images by resizing for instance. Uses Tesseract (OCR), Ollama (describe/choose most important words) and an NLP library (to extract keywords) to rename image files, giving them descriptive filenames.
Example use cases are screenshots or downloaded images, to be able to find them based on a textual search on the filename.

Used to require an API key and a path at Microsoft Azure, but since it's not possible to run this kind of thing locally at no extra cost that was preferred. 

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

### Prerequisits

There is need to install tesseract-ocr separately, for instance like this in linux:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-swe tesseract-ocr-deu
pip install -r requirements.txt
```

There is also need to install Ollama, and pulling the desired model. Default is `gemma3:4b-it-qat`.

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

###
Required step to ensure filter out keywords in English (change to your use case, also in the code):

```python -m spacy download en_core_web_sm```

### Still to do
* Facial recognition, RL training.

### Extra related scripts developed in the process

#### Image preprocessing
`resize_images.py`: Resizes images 50% and stores as jpeg (60% quality), suitable for downscaling screenshots for storage.

`scale_hor_50.py`: Resizes images horizontally in `scale_horizontally` folder, saves in `scaled_horizontally` folder. There are some presets that can be extended based on your use cases.

`crop.py`: Crops images based on presets defined in `cropping_modes.json`, see `sample_cropping_modes.json` for example and adapt to your use case. 

#### NLP and file preparations
`clean_file_name.py`: Changes from removing illegal charachters from the filename, and shortening it to enable transfer to Android (140 char limit), to just removing the words specified in the `words_to_remove.txt` list.

`name_extractor.py`: Extracts personal names from a body of text.

`words_to_set.py`: Reads a text file consisting of words you want to keep in the description, filters out words with numbers in them, removes duplicates, sorts the words and outputs a file with every words on a line of its own. Can be used to generate the word list files used by the main script, e.g. `words_to_include.txt` etc.
