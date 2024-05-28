# lambda-functions
aws lambda functions

## Features
- 이미지 resize
- 비디오 mp4 인코딩 / 썸네일 추출 / 해상도 조절

## Tech Stack 📚
<div style="margin-left: 1em">
    <img src="https://img.shields.io/badge/language-121011?style=for-the-badge"><img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white"><img src="https://img.shields.io/badge/3.12-515151?style=for-the-badge">
</div>
<div style="margin-left: 1em">
    <img src="https://img.shields.io/badge/public_cloud-121011?style=for-the-badge"><img src="https://img.shields.io/badge/aws_lambda-FF9900?style=for-the-badge&logo=aws-lambda&logoColor=white"><img src="https://img.shields.io/badge/amazon_s3-569A31?style=for-the-badge&logo=amazon-s3&logoColor=white">
</div>
<div style="margin-left: 1em">
    <img src="https://img.shields.io/badge/container-121011?style=for-the-badge"><img src="https://img.shields.io/badge/docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"><img src="https://img.shields.io/badge/4.30.0-515151?style=for-the-badge">
</div>
<div style="margin-left: 1em">
    <img src="https://img.shields.io/badge/docker_image-121011?style=for-the-badge"><img src="https://img.shields.io/badge/amazonlinux-FF9900?style=for-the-badge&logo=amazon&logoColor=white"><img src="https://img.shields.io/badge/2023-515151?style=for-the-badge">
</div>

## Dependencies
- pillow 10.3.0
    ```bash
    pip install pillow
    ```
- pillow_heif 0.16.0
    ```bash
    pip install pillow_heif
    ```
- filetype 1.2.0
    ```bash
    pip install filetype
    ```
- opencv 2
    ```bash
    pip install opencv-python
    ```
## Create container
1. docker 다운로드 : <a href="https://www.docker.com/products/docker-desktop/" target="_blank">docker-desktop</a>
2. ***docker run*** : 새로운 컨테이너를 생성하고 실행합니다.
    ```bash
    docker run -it -v /host/directory:/container/directory --name <컨테이너 이름> <이미지 이름>:<태그>
    ```
    - 예시 :
    ```bash
    docker run -it -v $(pwd):/lambda-layer --name amazonlinux2023 amazonlinux:2023
    ```
    - ***-it*** :
    ```text
    -it 옵션은 Docker 컨테이너를 실행할 때 주로 사용되는 두 가지 플래그를 결합한 것입니다. 각각의 플래그는 다음과 같은 역할을 합니다:
   
    1. -i (interactive) :
     1.1. -i 옵션은 컨테이너의 표준 입력(stdin)을 열어두어 인터랙티브 모드로 작동할 수 있게 합니다. 즉, 컨테이너가 사용자 입력을 받을 수 있게 해줍니다.
     1.2. 예를 들어, -i 옵션을 사용하면 터미널을 통해 컨테이너 내부에서 명령어를 입력할 수 있습니다.
    2. -t (tty) :
     2.1. -t 옵션은 가상 터미널을 할당합니다. 즉, 터미널 환경을 에뮬레이션하여 터미널 기반의 텍스트 인터페이스를 사용할 수 있게 해줍니다.
     2.2. 이를 통해 컨테이너 내부에서 터미널을 통해 입력과 출력을 관리할 수 있습니다.
   
    이 두 가지 옵션을 결합하여 -it로 사용하면, 인터랙티브한 터미널 세션을 열 수 있습니다. 이는 예를 들어, bash 쉘을 실행하여 컨테이너 내부에 접속하고 다양한 명령어를 실행할 때 유용합니다.
    ```
    - ***-v*** : 
    ```text
    컨테이너를 처음 실행할 때 docker run 명령어와 함께 -v 옵션을 사용하여 호스트와 컨테이너 간의 볼륨을 마운트할 수 있습니다. 이를 통해 호스트 파일 시스템의 일부를 컨테이너 내부에 마운트할 수 있습니다.
    ```

## Create layer packages
1. 디렉터리에 필요한 샘플 코드가 포함된 <a href="https://github.com/gjwnssud/lambda-functions" target="_blank">lambda-functions GitHub</a> 리포지토리를 복제합니다.
    ```bash
    git clone https://github.com/gjwnssud/lambda-functions.git
    ```
2. layer 디렉터리로 이동합니다.이 디렉터리에는 계층을 올바르게 생성하고 패키징하는 데 사용하는 스크립트가 포함되어 있습니다.
    ```text
    cd layer
    ```
3. ***requirements.txt*** 파일에 라이브러리에 포함하려는 종속성을 정의합니다.
    ```text
    pillow==10.3.0
    pillow_heif==0.16.0
    filetype==1.2.0
    ```
4. 두 스크립트를 모두 실행할 수 있는 권한이 있는지 확인하세요.
    ```bash
    chmod 744 1-install.sh && chmod 744 2-package.sh
    ```
5. 다음 명령을 사용하여 ***1-install.sh*** 스크립트를 실행하세요.
    ```bash
    ./1-install.sh
    ```
   - ***install.sh***
    ```text
    python3.12 -m venv create_layer
    source create_layer/bin/activate
    pip install -r requirements.txt
    ```
6. 다음 명령을 사용하여 ***2-package.sh*** 스크립트를 실행하세요.  
    ```bash
    ./2-package.sh.sh
    ```
   - ***2-package.sh***
    ```text
    mkdir python
    cp -r create_layer/lib python/
    zip -r layer_content.zip python
    ```
7. 출처 : <a href="https://docs.aws.amazon.com/ko_kr/lambda/latest/dg/python-layers.html" target="_blank">aws-documentation</a> 


## Contact
- hzn : gjwnssud@gmail.com
- project link : https://github.com/gjwnssud/lambda-functions
