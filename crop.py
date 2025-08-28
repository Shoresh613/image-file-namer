import os
import json
from PIL import Image

# Path to the JSON file with the modes
modes_file_path = 'cropping_modes.json'

# Read available modes from the file
try:
    with open(modes_file_path, 'r') as file:
        available_modes = json.load(file)
except FileNotFoundError:
    print(f"Error: The file {modes_file_path} was not found. Did you rename sample_cropping_modes.json to cropping_modes.json?")

def crop_image(input_path, output_path, mode_settings):
    with Image.open(input_path) as img:
        width, height = img.size
        left = mode_settings['left']
        upper = mode_settings['upper']
        right = eval(str(width) + mode_settings['right'].split('width')[1])
        lower = eval(str(height) + mode_settings['lower'].split('height')[1])
        cropped_img = img.crop((left, upper, right, lower))
        cropped_img.save(output_path, 'JPEG')

def process_directory(directory_path, output_directory, mode_settings):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
            input_path = os.path.join(directory_path, filename)
            output_path = os.path.join(output_directory, f"{os.path.splitext(filename)[0]}.jpg")
            crop_image(input_path, output_path, mode_settings)
            print(f"Processed and saved: {output_path}")

def print_menu_and_select_mode(modes):
    print("Please select a mode to use for cropping:")
    mode_keys = list(modes.keys())
    for i, mode in enumerate(mode_keys, 1):
        print(f"{i}. {mode}")
    while True:
        try:
            choice = int(input("Enter the number of the mode you wish to use: "))
            if 1 <= choice <= len(mode_keys):
                return modes[mode_keys[choice - 1]]
            else:
                print("Invalid selection. Please enter a number from the list.")
        except ValueError:
            print("Please enter a valid number.")

# Main script
if __name__ == "__main__":
    selected_mode_settings = print_menu_and_select_mode(available_modes)
    source_directory = './images/to_crop/'
    target_directory = './images/cropped/'
    process_directory(source_directory, target_directory, selected_mode_settings)
