import io
import json
import logging

import boto3
import filetype
from PIL import Image, ImageFile
from pillow_heif import register_heif_opener

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ImageFile.LOAD_TRUNCATED_IMAGES = True
register_heif_opener()

s3_client = boto3.client("s3")
temp_path = "contents/temp"
optimize_suffix = "_opt"


def lambda_handler(event, context):
    image_data = None
    status_code = 200
    job = {}

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    job["bucket"] = bucket_name
    job["key"] = object_key
    logger.info(f"filename = {object_key}")

    converted_object_key = object_key.replace(temp_path, temp_path + optimize_suffix)
    job["converted_key"] = converted_object_key

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        image_data = response['Body'].read()

        # file type 체크
        extension = filetype.guess_extension(image_data)
        logger.info(f"file type = {extension}")
        if extension not in list(map(lambda s: str.replace(s, ".", ""), Image.registered_extensions().keys())):
            raise ValueError(f"Unsupported image format: {extension}")

        buffer = io.BytesIO()
        image = Image.open(io.BytesIO(image_data))
        if extension in ["heif", "heic"]:  # heif, heic 포맷일 경우 jpg로 컨버팅
            image.save(buffer, "JPEG")
            logger.info(f"heif to jpg convert complete. image format = {Image.open(buffer).format}")
        else:
            image.save(buffer, image.format)
        buffer.seek(0)

        # 변환된 이미지를 S3 버킷에 저장
        logger.info(f"converted filename = {converted_object_key}")
        s3_client.put_object(Bucket=bucket_name, Key=converted_object_key, Body=buffer)
    except Exception as e:
        logger.error(f"Exception = {e}")
        status_code = 500
        job["error_msg"] = e

        # 원본 이미지를 그대로 저장
        logger.info(f"converted filename = {converted_object_key}")
        s3_client.put_object(Bucket=bucket_name, Key=converted_object_key, Body=io.BytesIO(image_data))
        raise
    finally:
        return {
            'statusCode': status_code,
            'body': json.dumps(job, indent=4, sort_keys=True, default=str)
        }
