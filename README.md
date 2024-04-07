# image-file-namer

Simple script that uses Azure AI Vision (to get a textual description) and a local NLP library (to extract keywords) to rename image files, giving them descriptive filenames.
Example use cases are screenshots or downloaded images, to be able to find them based on a textual search on the filename.

It requires an API key and path at MicroSoft Azure that you need to set as environment variables (see below). 
Naturally, there is a cost involved for using the API, unless you happen to be a student, in which case you get 5000 such API calls for free each months. 

The script makes sure it doesn't exceed the limit of 20 API calls per minute (2 calls for every image which leads to a processing speed of 9 images per minute to be on the safe side). It does not keep track of exceeding 5000 per month, but if more calls are made, they will simply be refused unless you pay for more.

Words to remove from the filenames are based on English and Swedish, but can easily be updated.

**Example:**

![Example Image](assets/States%20CIA%20United%20LTG%20America%20Morrell%20director%20Mike%20deputy%2020230422%20nypos%20Flynn.jpg "Example image")

Generated filename: `"States CIA United LTG America Morrell director Mike deputy 20230422 nypos Flynn.jpg"`

### Folders
All relative to the git directory:

| Folder Path             | Description                            |
|-------------------------|----------------------------------------|
| `./images/`             | Place images here to automatically get them renamed |
| `./images/named_images` | Named images are stored here           |

### Environment variables
| Variable               | Brief Description                                  |
|------------------------|----------------------------------------------------|
| `AZURE_IMAGE_ENDPOINT` | Endpoint URL for the Azure Image service           |
| `AZURE_IMAGE_KEY`      | Authentication key for accessing the Azure Image service |