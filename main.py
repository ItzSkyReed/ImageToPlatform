import base64
import zlib
import json
from collections.abc import Sequence
from pathlib import Path
import argparse
import pyperclip
from PIL import Image, ImageOps


def write_json_structure(icon_name: str | Path):
    blueprint = {
        "blueprint": {
            "label": icon_name,
            "icons": [
                {
                    "signal": {
                        "name": "space-platform-foundation"
                    },
                    "index": 1
                }
            ],
            "item": "blueprint",
            "version": 562949954994181  # Factorio version (currently, stable 2.0.24)
        }
    }
    return blueprint

def calculate_proportional_size(image, width=None, height=None):
    orig_width, orig_height= image.size
    if width is not None and height is None:
        height = int(round((width / orig_width) * orig_height, 0))
    elif height is not None and width is None:
        width = int(round((height / orig_height) * orig_width, 0))
    return width, height

def process_image(image_path: Path, invert: bool = False, height: int = None, width: int = None):
    img = Image.open(image_path)
    if height or width:
        if not (width and height):
            width, height = calculate_proportional_size(img, width=width, height=height)

        img = img.resize((width, height), Image.Resampling.HAMMING)

    if invert:
        img = ImageOps.invert(img.convert("RGB"))

    return img


def rgba_image_to_boolean_matrix(image: Image.Image):
    width, height = image.size
    pixel_data = image.load()

    boolean_matrix = []
    for y in range(height):
        row = []
        for x in range(width):
            pixel_value = pixel_data[x, y]
            row.append(pixel_value[3] != 0)  # Alpha Channel Check
        boolean_matrix.append(row)

    return boolean_matrix


def non_rgba_image_to_boolean_matrix(image: Image.Image, threshold=128):
    width, height = image.size
    pixel_data = image.load()

    boolean_matrix = []
    for y in range(height):
        row = []
        for x in range(width):
            pixel_value = pixel_data[x, y]
            row.append(pixel_value >= threshold)
        boolean_matrix.append(row)

    return boolean_matrix

def generate_blueprint(matrix: Sequence[Sequence[bool]], json_dict: dict):
    tiles = []
    for y in range(len(matrix)):
        for x in range(len(matrix[y])):
            if matrix[y][x]:
                tiles.append({
                    "position": {
                        "x": x,
                        "y": y
                    },
                    "name": "space-platform-foundation"
                })

    json_dict['blueprint']['tiles'] = tiles
    return json.dumps(json_dict, indent=4)


def convert_image_to_matrix(image: Image.Image, threshold: int = 128):
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        return rgba_image_to_boolean_matrix(image.convert("RGBA"))
    else:
        grayscale_image = image.convert("L")
        return non_rgba_image_to_boolean_matrix(grayscale_image, threshold)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=str, help="Path to image")
    parser.add_argument("-W", "--width", type=int, default=None, help="Width of the image for conversion", required=False)
    parser.add_argument("-H", "--height", type=int, default=None, help="Height of the image for conversion", required=False)
    parser.add_argument("-I", "--invert", action="store_true", help="Invert the colors of the image", required=False, default=False)
    parser.add_argument("-T", "--threshold", type=int, default=128, required=False, help="Threshold value for grayscale conversion (0-255), default is 128")
    args = parser.parse_args()

    if not (0 <= args.threshold <= 255):
        raise Exception("Threshold value must be between 0 and 255")

    input_path = Path(args.file_path)
    if not input_path.is_file():
        raise Exception(f"File not found: {input_path}")

    image = process_image(input_path, args.invert, args.width, args.height)
    image_matrix = convert_image_to_matrix(image, threshold=args.threshold)

    blueprint_json_str = generate_blueprint(image_matrix, write_json_structure(input_path.stem))

    encoded_string = "0" + base64.b64encode(zlib.compress(blueprint_json_str.encode())).decode()
    pyperclip.copy(encoded_string)

    print("Blueprint string is copied to clipboard.")


if __name__ == "__main__":
    main()
