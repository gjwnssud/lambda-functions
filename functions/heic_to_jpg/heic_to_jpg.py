import io
import logging

import filetype
from PIL import Image, ImageFile
from pillow_heif import register_heif_opener

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ImageFile.LOAD_TRUNCATED_IMAGES = True
register_heif_opener()


def get_mime_type(image_data):
    guess = filetype.guess(image_data)
    print(f"extension = {guess.extension}")
    print(f"mime type = {guess.mime}")


def heic_to_jpg(src):
    get_mime_type(open(src, "rb").read())
    heic_image = Image.open(src)
    buffer = io.BytesIO()
    heic_image.save(buffer, "JPEG")
    get_mime_type(buffer)


if __name__ == '__main__':
    # heic_to_jpg("/Users/hzn/Downloads/03011F13-CC9D-48FB-B191-D14C2DA23A6C.jpeg")
    filepath = "/Users/hzn/temp/1-heic-test.jpeg"
    print(f"type = {type(Image.open(filepath))}")
    print(f"type = {type(open(filepath, "rb"))}")
    print(f"type = {type(open(filepath, "rb").read())}")
    get_mime_type(filepath)
