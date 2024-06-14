import json
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger()
logger.setLevel(logging.INFO)
response = {"statusCode": 200, "headers": {"Content-Type": "application/json"}}


def lambda_handler(event, context):
    query_params = event.get("queryStringParameters", {})
    logger.info(f"query_params = {query_params}")
    driver = None
    try:
        url = query_params["url"]
        logger.info(f"url = {url}")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = "/opt/bin/google-chrome"
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

        service = webdriver.ChromeService(executable_path="/opt/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)
        # WebDriverWait을 사용하여 og:로 시작하는 meta 태그가 로드될 때까지 대기
        WebDriverWait(driver, 5).until(
                ec.presence_of_element_located((By.XPATH, "//meta[starts-with(@property, 'og:')]"))
        )
        logger.info(f"complete crawling. page source = {driver.page_source}")
        response["body"] = json.dumps({
            "message": "Success.",
            "pageSource": driver.page_source
        })
    except Exception as e:
        logger.error(f"Exception = {e}")
        response["statusCode"] = 500
        response["body"] = json.dumps({
            "message": str(e)
        })
    finally:
        if driver is not None:
            driver.quit()

    return response
