import boto3
from PIL import Image, ImageFile, ImageSequence, ExifTags
from pillow_heif import register_heif_opener
import filetype
import io
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ImageFile.LOAD_TRUNCATED_IMAGES = True
register_heif_opener()

s3_client = boto3.client("s3")

contents_path = "contents/release"
post_path = contents_path + "/post"
reply_path = contents_path + "/reply"
profile_path = "profile"
creator_profile_path = "creator/" + profile_path
background_path = "background"
optimize_suffix = "_opt"


def lambda_handler(event, context):
    status_code = 200
    resized_object_key_prefix = None
    job = {}

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    job["bucket"] = bucket_name
    job["key"] = object_key

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        image_data = response['Body'].read()
        # 파일 형식 확인
        try:
            image = Image.open(io.BytesIO(image_data))
            image_format = image.format
            logger.info(f"Image format: {image_format}")
        except Exception as e:
            logger.error(f"Error determining image format: {e}")
            raise ValueError("Unsupported image format")

        # 확장자 확인 및 맞춤 처리
        valid_extensions = ['JPEG', 'JPG', 'PNG', 'GIF', 'BMP']
        if image_format.upper() not in valid_extensions:
            raise ValueError(f"Unsupported image format: {image_format}")

        job["size"] = image.size

        # EXIF 데이터 처리 (회전 방지)
        try:
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    exif = dict(exif.items())
                    orientation_key = [key for key, value in ExifTags.TAGS.items() if value == 'Orientation']
                    if orientation_key:
                        orientation = exif.get(orientation_key[0])
                        if orientation == 3:
                            image = image.rotate(180, expand=True)
                        elif orientation == 6:
                            image = image.rotate(270, expand=True)
                        elif orientation == 8:
                            image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError) as e:
            # EXIF 데이터가 없거나 처리 중 오류 발생 시
            logger.warning(f"No EXIF orientation data found or error processing EXIF: {e}")

        width, height = image.size
        logger.info(f"filename = {object_key}, original width = {width}, original height = {height}")

        ratio = None
        if post_path in object_key:
            if width > 960:
                ratio = 960 / width
                width = 960
            resized_object_key_prefix = post_path
        elif reply_path in object_key:
            if width > 650:
                ratio = 650 / width
                width = 650
            resized_object_key_prefix = reply_path
        elif creator_profile_path in object_key:
            if width > 726:
                ratio = 726 / width
                width = 726
            resized_object_key_prefix = creator_profile_path
        elif profile_path in object_key:
            if width > 356:
                ratio = 356 / width
                width = 356
            resized_object_key_prefix = profile_path
        elif background_path in object_key:
            if width > 1200:
                ratio = 1200 / width
                width = 1200
            resized_object_key_prefix = background_path

        # 리사이즈 정의
        if ratio is not None:
            height = int(height * ratio)
        job["resize"] = (width, height)

        # 이미지, GIF 구분 후 리사이징
        buffer = io.BytesIO()  # byte 버퍼 생성
        if image_format.upper() == 'GIF':
            frames = []
            durations = []
            for frame in ImageSequence.Iterator(image):
                resized_frame = frame.copy()
                resized_frame = resized_frame.resize((width, height))
                frames.append(resized_frame)
                durations.append(frame.info['duration'])
            frames[0].save(buffer, format=image_format, save_all=True, append_images=frames[1:], optimize=False, duration=durations, loop=0)
        else:
            image = image.resize((width, height))
            image.save(buffer, format=image_format)
        buffer.seek(0)

        # 리사이즈한 이미지를 S3 버킷에 저장
        resized_object_key = object_key.replace(resized_object_key_prefix, resized_object_key_prefix + optimize_suffix)
        job["resized_key"] = resized_object_key
        logger.info(f"resized filename = {resized_object_key}, resized width = {width}, resized height = {height}")
        s3_client.put_object(Bucket=bucket_name, Key=resized_object_key, Body=buffer)
    except Exception as e:
        logger.error(f"Exception = {e}")
        status_code = 500
        job["error_msg"] = e
        raise
    finally:
        return {
            'statusCode': status_code,
            'body': json.dumps(job, indent=4, sort_keys=True, default=str)
        }


def get_mime_type(image_data):
    guess = filetype.guess(image_data)
    print(f"extension = {guess.extension}")
    print(f"mime type = {guess.mime}")


if __name__ == '__main__':
    # print(Image.open("/Users/hzn/Downloads/03011F13-CC9D-48FB-B191-D14C2DA23A6C.jpeg").format)
    # get_mime_type(open("/Users/hzn/Downloads/03011F13-CC9D-48FB-B191-D14C2DA23A6C.jpeg", "rb").read())
    # print(list(set(Image.registered_extensions().values())))
    # print(Image.registered_extensions().keys())

    print(list(map(lambda s: str.replace(s, ".", ""), Image.registered_extensions().keys())))
