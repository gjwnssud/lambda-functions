import logging
import os
import uuid

import cv2

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(input_path):
    slash_last_index = input_path.rfind("/")
    dot_last_index = input_path.rfind(".")
    resized_output_path_prefix = input_path[0:slash_last_index + 1]
    filename = input_path[slash_last_index + 1:dot_last_index]
    # 썸네일 추출
    thumbnail_path = resized_output_path_prefix + "thumbnail/"
    thumbnail_filename = "{}.{}".format(uuid.uuid4(), "jpg")
    height = extract_thumbnail(input_path, thumbnail_path, thumbnail_filename)
    # 리사이즈 및 mp4 인코딩
    resized_output_path = resized_output_path_prefix + "resized/"
    # resize_and_mp4encode_video(input_path, resized_output_path, filename + ".mp4", 960, int(height))
    resize_and_mp4encode_video(input_path, resized_output_path, filename + ".mp4", 960, 540)


def resize_and_mp4encode_video(input_path, output_path, filename, width, height):
    # 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(input_path)

    # 출력 비디오의 FourCC 코드 정의 (MP4V를 사용)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    # 비디오 쓰기 객체 생성
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    out = cv2.VideoWriter(output_path + filename, fourcc, cap.get(cv2.CAP_PROP_FPS), (width, height))

    while True:
        # 프레임별로 읽기
        ret, frame = cap.read()
        if not ret:
            break  # 읽을 프레임이 없으면 종료

        # 프레임 크기 조절
        resized_frame = cv2.resize(frame, (width, height))

        # 조절된 프레임을 새로운 비디오 파일에 쓰기
        out.write(resized_frame)

    # 모든 자원 해제
    cap.release()
    out.release()
    cv2.destroyAllWindows()


def extract_thumbnail(video_path, output_path, thumbnail_filename, frame_number=2):
    cap = cv2.VideoCapture(video_path)
    frame_height = None

    if not cap.isOpened():
        logger.error("Error opening video file")
    else:
        cap.set(1, frame_number)  # 2번째 프레임으로 설정
        ret, frame = cap.read()
        if ret:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            cv2.imwrite(output_path + thumbnail_filename, frame)
            frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        cap.release()

    return frame_height


if __name__ == "__main__":
    # lambda_handler("/Users/hzn/temp/b211ea3ca1ec480d01ef.mov")
    print(f"{uuid.uuid4()}")
