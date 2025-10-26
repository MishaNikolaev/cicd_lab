import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

@pytest.fixture(scope="session")
def driver():
    """Фикстура для настройки WebDriver"""
    chrome_options = Options()
    
    # Настройки для headless режима в Docker
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    
    # Отключение проверки SSL сертификатов
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Настройка для работы с HTTPS
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Отключение предупреждений о безопасности
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Настройка для работы с самоподписанными сертификатами
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    
    # Попытка использовать системный Chrome или Chromium
    try:
        # Сначала попробуем использовать системный chromedriver
        if os.path.exists("/var/jenkins_home/workspace/chromedriver/chromedriver"):
            service = Service("/var/jenkins_home/workspace/chromedriver/chromedriver")
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Если системный chromedriver недоступен, используем webdriver-manager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Ошибка при создании WebDriver: {e}")
        # Fallback - попробуем без service
        driver = webdriver.Chrome(options=chrome_options)
    
    # Настройка таймаутов
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(30)
    
    yield driver
    
    # Закрытие драйвера после тестов
    driver.quit()
