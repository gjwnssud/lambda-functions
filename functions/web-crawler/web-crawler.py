from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def crawling(url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    driver = None
    try:
        service = Service('chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)

        # WebDriverWait을 사용하여 og:로 시작하는 meta 태그가 로드될 때까지 대기
        WebDriverWait(driver, 5).until(
                ec.presence_of_element_located((By.XPATH, "//meta[starts-with(@property, 'og:')]"))
        )

        elements = driver.find_elements(By.XPATH, "//meta[starts-with(@property, 'og:')]")
        for element in elements:
            attribute = element.get_attribute("property")
            content = element.get_attribute("content")
            if attribute:
                print(f"Meta tag: {attribute} = {content}")

    except Exception as e:
        print(f"Exception = {e}")
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    crawling('https://x.com/historyinmemes/status/1800276754143252740')
