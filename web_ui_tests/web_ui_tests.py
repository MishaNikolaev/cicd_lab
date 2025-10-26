import pytest
import time
import requests
from selenium.webdriver.common.by import By

def check_openbmc_availability():
    try:
        response = requests.get("https://localhost:2443", verify=False, timeout=5)
        return response.status_code in [200, 401, 403, 404]
    except:
        return False

@pytest.mark.usefixtures("driver")
def test_openbmc_auth(driver):
    try:
        driver.get("https://localhost:2443")
        time.sleep(3)

        inputs = driver.find_elements(By.TAG_NAME, "input")

        username_field = None
        password_field = None
        for inp in inputs:
            field_type = inp.get_attribute("type")
            if field_type == "text":
                username_field = inp
            elif field_type == "password":
                password_field = inp

        if username_field and password_field:
            username_field.send_keys("root")
            password_field.send_keys("0penBmc")

        login_button = None
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Log in" in btn.text:
                login_button = btn
                break
        if login_button:
            login_button.click()

        time.sleep(5)
        current_url = driver.current_url

        if current_url != "https://localhost:2443/#/login":
            result = True
        else:
            try:
                main_page_elements = driver.find_elements(By.XPATH,
                                                          "//*[contains(text(), 'System') or contains(text(), 'Dashboard') or contains(text(), 'Overview')]")
                if main_page_elements:
                    result = True
                else:
                    result = False
            except:
                result = False
        
        assert result, "Тест авторизации не пройден"

        screenshot_name = "test1_success.png" if result else "test1_failed.png"
        driver.save_screenshot(screenshot_name)

    except Exception as e:
        driver.save_screenshot("test1_failed.png")
        assert False, f"Ошибка в тесте авторизации: {e}"

@pytest.mark.usefixtures("driver")
def test_block_account(driver):
    try:
        driver.get("https://localhost:2443")
        time.sleep(3)

        inputs = driver.find_elements(By.TAG_NAME, "input")

        username_field = None
        password_field = None
        for inp in inputs:
            field_type = inp.get_attribute("type")
            if field_type == "text":
                username_field = inp
            elif field_type == "password":
                password_field = inp

        if username_field and password_field:
            username_field.send_keys("root")
            password_field.send_keys("wrong_password")

        login_button = None
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Log in" in btn.text:
                login_button = btn
                break
        if login_button:
            login_button.click()

        time.sleep(5)

        error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Invalid') or contains(text(), 'Error') or contains(text(), 'Failed')]")
        
        if error_elements:
            result = True
        else:
            current_url = driver.current_url
            if current_url == "https://localhost:2443/#/login":
                result = True
            else:
                result = False

        assert result, "Тест блокировки аккаунта не пройден"

        screenshot_name = "test2_success.png" if result else "test2_failed.png"
        driver.save_screenshot(screenshot_name)

    except Exception as e:
        driver.save_screenshot("test2_failed.png")
        assert False, f"Ошибка в тесте блокировки аккаунта: {e}"

@pytest.mark.usefixtures("driver")
def test_fans_temp(driver):
    try:
        driver.get("https://localhost:2443")
        time.sleep(3)

        inputs = driver.find_elements(By.TAG_NAME, "input")

        username_field = None
        password_field = None
        for inp in inputs:
            field_type = inp.get_attribute("type")
            if field_type == "text":
                username_field = inp
            elif field_type == "password":
                password_field = inp

        if username_field and password_field:
            username_field.send_keys("root")
            password_field.send_keys("0penBmc")

        login_button = None
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Log in" in btn.text:
                login_button = btn
                break
        if login_button:
            login_button.click()

        time.sleep(5)

        try:
            fans_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Fan') or contains(text(), 'fan')]")
            temp_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Temperature') or contains(text(), 'Temp') or contains(text(), 'temperature')]")
            
            if fans_elements or temp_elements:
                result = True
            else:
                result = False
        except:
            result = False

        assert result, "Тест вентиляторов и температуры не пройден"

        screenshot_name = "test3_success.png" if result else "test3_failed.png"
        driver.save_screenshot(screenshot_name)

    except Exception as e:
        driver.save_screenshot("test3_failed.png")
        assert False, f"Ошибка в тесте вентиляторов и температуры: {e}"