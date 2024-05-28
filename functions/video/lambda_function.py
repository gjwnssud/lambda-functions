import json
import logging
import os
import uuid

import boto3
import cv2

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

s3_contents_path = "contents/input/{}"
s3_thumbnail_path = "contents/media/{}/Default/Thumbnails/"
s3_encoded_path = "contents/media/{}/Default/MP4/"
download_root = "/tmp/video/"


def lambda_handler(event, context):
    status_code = 200
    job = {}

    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    job["bucket"] = bucket_name
    job["key"] = object_key

    try:
        # 임시 파일 경로 생성
        download_path = download_root + "{}{}".format(uuid.uuid4(), object_key)

        # 파일 다운로드
        s3_client.download_file(bucket_name, object_key, download_path)

        # 파일 정보 추출, filename = UUID
        path_prefix, filename = extract_file_info(download_path)

        # 썸네일 추출
        thumbnail_path = path_prefix + "thumbnail/"
        thumbnail_filename = "{}.0000001.{}".format(filename, "jpg")
        extract_thumbnail(download_path, thumbnail_path, thumbnail_filename, job)

        # 리사이즈 및 mp4 인코딩
        encoded_path = path_prefix + "encoded/"
        encoded_filename = filename + ".mp4"
        resize_and_mp4encode_video(download_path, encoded_path, encoded_filename)

        # 파일 업로드
        thumbnail_object_key = object_key.replace(s3_contents_path.format(filename), s3_thumbnail_path.format(filename) + thumbnail_filename)
        job["thumbnail_object_key"] = thumbnail_object_key
        s3_client.upload_file(thumbnail_path + thumbnail_filename, bucket_name, thumbnail_object_key)
        encoded_object_key = object_key.replace(s3_contents_path.format(filename), s3_encoded_path.format(filename) + encoded_filename)
        job["encoded_object_key"] = encoded_object_key
        s3_client.upload_file(encoded_path + encoded_filename, bucket_name, thumbnail_object_key)

        # 임시 파일 삭제
        remove_file(download_root)
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


def resize_and_mp4encode_video(input_path, output_path, filename):
    # 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(input_path)
    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 출력 비디오의 FourCC 코드 정의 (MP4V를 사용)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    # 비디오 쓰기 객체 생성
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    out = cv2.VideoWriter(output_path + filename, fourcc, cap.get(cv2.CAP_PROP_FPS), (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if width > 960:
            # 프레임 크기 조절
            frame = cv2.resize(frame, (960, height))

        # 조절된 프레임을 새로운 비디오 파일에 쓰기
        out.write(frame)

    # 모든 자원 해제
    cap.release()
    out.release()


def extract_thumbnail(input_path, output_path, thumbnail_filename, job, frame_number=2):
    cap = cv2.VideoCapture(input_path)
    cap.set(1, frame_number)  # 2번째 프레임으로 설정

    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ret, frame = cap.read()
    if ret:
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        if width > 960:
            width = 960
            frame = cv2.resize(frame, (width, height))

        cv2.imwrite(output_path + thumbnail_filename, frame)
    cap.release()
    job["resize"] = width, height


def extract_file_info(input_path):
    slash_last_index = input_path.rfind("/")
    dot_last_index = input_path.rfind(".")
    path = input_path[0:slash_last_index + 1]
    filename = input_path[slash_last_index + 1:dot_last_index]

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        logger.error("Error opening video file")
        raise Exception("Error opening video file")

    return path, filename


def remove_file(path):
    if os.path.exists(path):
        if os.path.isfile(path):
            os.remove(path)
        else:
            files = os.listdir(path)
            for file in files:
                remove_file(file)
            os.rmdir(path)
