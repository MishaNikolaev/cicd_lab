import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os

@pytest.fixture(scope="session")
def driver():
    chrome_options = Options()
    
    # Основные настройки для headless режима
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Настройки для игнорирования SSL ошибок
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    
    # Дополнительные настройки для стабильности
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    
    # Настройки для обхода автоматизации
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Поиск Chrome/Chromium
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser", 
        "/usr/bin/chromium",
        "/usr/bin/chrome"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_options.binary_location = path
            break
    
    try:
        # Попробуем без service сначала
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        try:
            # Если не получилось, попробуем с service
            service = Service("/usr/local/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e2:
            print(f"Ошибка при создании WebDriver: {e2}")
            pytest.skip("WebDriver недоступен")
    
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(30)
    
    yield driver
    
    driver.quit()
