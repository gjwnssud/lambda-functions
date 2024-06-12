import io
import json
import logging

import boto3
import filetype
from PIL import Image, ImageFile, ImageSequence, ExifTags
from pillow_heif import register_heif_opener

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
crtr_notice_path = contents_path + "/crtr_notice"
optimize_suffix = "_opt"


def lambda_handler(event, context):
    image_data = None
    status_code = 200
    job = {}

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    job["bucket"] = bucket_name
    job["key"] = object_key

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        image_data = response['Body'].read()

        # file type 체크
        extension = filetype.guess_extension(image_data)
        logger.info(f"file type = {extension}")
        if extension not in list(map(lambda s: str.replace(s, ".", ""), Image.registered_extensions().keys())):
            raise ValueError(f"Unsupported image format: {extension}, object key = {object_key}")

        image = Image.open(io.BytesIO(image_data))
        # heif, heic일 경우 jpg로 변환
        if extension in ["heif", "heic"]:
            buffer = io.BytesIO()
            image.save(buffer, "JPEG")
            image = Image.open(buffer)
            logger.info(f"heif to jpg convert complete. image format = {image.format}")
        original_width, original_height = image.size
        logger.info(f"filename = {object_key}, original width = {original_width}, original height = {original_height}")

        image_format = image.format
        # EXIF 데이터 처리 (회전 방지)
        try:
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    exif = dict(exif.items())
                    orientation_key = [key for key, value in ExifTags.TAGS.items() if value == 'Orientation']
                    if orientation_key:
                        orientation = exif.get(orientation_key[0])
                        logger.info(f"orientation : {orientation}")
                        if orientation == 2:
                            image = image.transpose(Image.FLIP_LEFT_RIGHT)
                        elif orientation == 3:
                            image = image.rotate(180, expand=True)
                        elif orientation == 4:
                            image = image.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
                        elif orientation == 5:
                            image = image.rotate(270, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                        elif orientation == 6:
                            image = image.rotate(270, expand=True)
                        elif orientation == 7:
                            image = image.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                        elif orientation == 8:
                            image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError) as e:
            # EXIF 데이터가 없거나 처리 중 오류 발생 시
            logger.warning(f"No EXIF orientation data found or error processing EXIF: {e}")

        width, height = image.size
        job["size"] = image.size

        ratio = None
        if post_path in object_key or crtr_notice_path in object_key:
            if width > 960:
                ratio = 960 / width
                width = 960
        elif reply_path in object_key:
            if width > 650:
                ratio = 650 / width
                width = 650
        elif creator_profile_path in object_key:
            if width > 726:
                ratio = 726 / width
                width = 726
        elif profile_path in object_key:
            if width > 356:
                ratio = 356 / width
                width = 356
        elif background_path in object_key:
            if width > 1200:
                ratio = 1200 / width
                width = 1200

        # 리사이즈 정의
        if ratio is not None:
            height = int(height * ratio)
        job["resize"] = (width, height)

        # 이미지, GIF 구분 후 리사이징
        # image_format = image.format
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
        resized_object_key = get_resized_object_key(object_key)
        job["resized_key"] = resized_object_key
        logger.info(f"resized filename = {resized_object_key}, resized width = {width}, resized height = {height}")
        s3_client.put_object(Bucket=bucket_name, Key=resized_object_key, Body=buffer)
    except Exception as e:
        logger.error(f"Exception = {e}")
        status_code = 500
        job["error_msg"] = e

        # 원본 이미지를 그대로 저장
        s3_client.put_object(Bucket=bucket_name, Key=get_resized_object_key(object_key), Body=io.BytesIO(image_data))
        raise
    finally:
        return {
            'statusCode': status_code,
            'body': json.dumps(job, indent=4, sort_keys=True, default=str)
        }


def get_resized_object_key(object_key):
    resized_object_key_prefix = None
    if post_path in object_key:
        resized_object_key_prefix = post_path
    elif reply_path in object_key:
        resized_object_key_prefix = reply_path
    elif creator_profile_path in object_key:
        resized_object_key_prefix = creator_profile_path
    elif profile_path in object_key:
        resized_object_key_prefix = profile_path
    elif background_path in object_key:
        resized_object_key_prefix = background_path
    elif crtr_notice_path in object_key:
        resized_object_key_prefix = crtr_notice_path
    return object_key.replace(resized_object_key_prefix, resized_object_key_prefix + optimize_suffix)
