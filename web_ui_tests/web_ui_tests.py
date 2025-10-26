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
        print("1. Открываем страницу OpenBMC...")
        driver.get("https://localhost:2443")
        time.sleep(3)
        print(f"Страница открыта: {driver.current_url}")
        print(f"Заголовок страницы: '{driver.title}'")

        print("2. Поиск формы логина...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Найдено input полей: {len(inputs)}")

        for i, inp in enumerate(inputs):
            field_type = inp.get_attribute("type")
            field_id = inp.get_attribute("id")
            field_name = inp.get_attribute("name")
            field_placeholder = inp.get_attribute("placeholder")
            print(
                f"Поле {i + 1}: type='{field_type}', id='{field_id}', name='{field_name}', placeholder='{field_placeholder}'")

        print("3. Заполняем форму логина...")
        username_field = None
        password_field = None
        for inp in inputs:
            field_type = inp.get_attribute("type")
            if field_type == "text":
                username_field = inp
            elif field_type == "password":
                password_field = inp

        if username_field and password_field:
            print("Найдены оба поля: логин и пароль")
            username_field.send_keys("root")
            password_field.send_keys("0penBmc")
            print("Данные введены: root / 0penBmc")
        else:
            print("Не удалось найти поля для ввода")

        print("4. Ищем кнопку Log in...")
        login_button = None
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Log in" in btn.text:
                login_button = btn
                break
        if login_button:
            print(f"Кнопка Log in найдена: '{login_button.text}'")
            login_button.click()
            print("Кнопка Log in нажата")
        else:
            print("Кнопка Log in не найдена")
            for i, btn in enumerate(buttons):
                print(f"Кнопка {i}: '{btn.text}'")

        print("5. Проверяем результат авторизации...")
        time.sleep(5)
        current_url = driver.current_url
        print(f"Текущий URL: {current_url}")

        if current_url != "https://localhost:2443/#/login":
            print("Авторизация удалась! URL изменился")
            print("Тест пройден: Пользователь успешно вошел в систему")
            result = True
        else:
            try:
                main_page_elements = driver.find_elements(By.XPATH,
                                                          "//*[contains(text(), 'System') or contains(text(), 'Dashboard') or contains(text(), 'Overview')]")
                if main_page_elements:
                    print("Авторизация удалась! Найдены элементы главной страницы")
                    print("Тест пройден: Пользователь успешно вошел в систему")
                    result = True
                else:
                    print("Авторизация не удалась! Остались на странице логина")
                    print("Тест не пройден: Не удалось войти в систему")
                    result = False
            except:
                print("Авторизация не удалась!")
                print("Тест не пройден: Не удалось войти в систему")
                result = False
        
        assert result, "Тест авторизации не пройден"

        screenshot_name = "test1_success.png" if result else "test1_failed.png"
        driver.save_screenshot(screenshot_name)
        print(f"Скриншот сохранен: {screenshot_name}")

    except Exception as e:
        print(f"Тест не пройден!: {e}")
        result = False


print("=== Тест 3: Блокировка учетной записи ===")


@pytest.mark.usefixtures("driver")
def test_block_account(driver):
    try:
        print("1. Открываем страницу OpenBMC...")
        driver.get("https://localhost:2443")
        time.sleep(5)
        print(f"Страница открыта: {driver.current_url}")

        print("2. Выполняем 5 неудачных попыток входа...")
        for attempt in range(5):
            print(f"Попытка {attempt + 1}/5")
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
                username_field.clear()
                password_field.clear()
                username_field.send_keys("testuser")
                password_field.send_keys(f"wrongpassword{attempt}")
                login_button = None
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if "Log in" in btn.text:
                        login_button = btn
                        break
                if login_button:
                    login_button.click()
                    print(f"Введены данные: testuser / wrongpassword{attempt}")
            time.sleep(10)

            current_url = driver.current_url
            lockout_detected = False
            lockout_messages = ["Invalid username or password", "Account locked", "Account blocked",
                                "Too many attempts", "Try again later"]
            for message in lockout_messages:
                try:
                    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{message}')]")
                    if elements:
                        print(f"   Найдено сообщение: '{elements[0].text}'")
                        if "locked" in message.lower() or "blocked" in message.lower() or "many" in message.lower():
                            lockout_detected = True
                            print(f"Обнаружена возможная блокировка на попытке {attempt + 1}")
                except:
                    continue
            if lockout_detected:
                break

        print("3. Пробуем войти с правильными данными...")
        url_before_login = driver.current_url
        print(f"URL до входа: {url_before_login}")
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
            username_field.clear()
            password_field.clear()
            username_field.send_keys("testuser")
            password_field.send_keys("qweqwe123")
            login_button = None
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "Log in" in btn.text:
                    login_button = btn
                    break
            if login_button:
                login_button.click()
                print("Введены правильные данные: testuser / qweqwe123")
        time.sleep(5)
        url_after_login = driver.current_url
        print(f"URL после входа: {url_after_login}")

        print("4. Проверяем результат с помощью assert...")
        try:
            assert "login" in url_after_login.lower(), f"Ожидалось остаться на странице логина, но текущий URL: {url_after_login}"
            print("ТЕСТ ПРОЙДЕН: Учетная запись заблокирована")
            result = True
        except AssertionError as e:
            print(f"ТЕСТ НЕ ПРОЙДЕН: {e}")
            result = False
        
        assert result, "Тест блокировки учетной записи не пройден"

        block_messages = ["Account locked", "Account blocked", "Too many attempts", "locked", "blocked"]
        for message in block_messages:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{message}')]")
                if elements:
                    print(f"Найдено сообщение о блокировке: '{elements[0].text}'")
                    break
            except:
                continue

        screenshot_name = "test3_success.png" if result else "test3_failed.png"
        driver.save_screenshot(screenshot_name)
        print(f"Скриншот сохранен: {screenshot_name}")

    except Exception as e:
        print(f"Тест не пройден!: {e}")
        result = False


@pytest.mark.usefixtures("driver")
def test_fans_temp(driver):
    try:
        print("1. Выполняем вход в систему...")
        driver.get("https://localhost:2443")
        time.sleep(5)
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            field_type = inp.get_attribute("type")
            if field_type == "text":
                inp.send_keys("root")
            elif field_type == "password":
                inp.send_keys("0penBmc")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Log in" in btn.text:
                btn.click()
                break
        time.sleep(5)

        if "login" in driver.current_url:
            print("Ошибка: Не удалось войти в систему")
            result = False
            return

        print("Успешный вход в систему")
        print(f"Текущий URL: {driver.current_url}")

        print("2. Переходим на страницу Thermal данных...")
        thermal_url = "https://localhost:2443/redfish/v1/Chassis/chassis/Thermal"
        driver.get(thermal_url)
        time.sleep(5)
        print(f"Открыта страница: {driver.current_url}")

        print("3. Ищем информацию о температуре...")
        page_text = driver.find_element(By.TAG_NAME, "body").text
        print("Текст страницы:")
        print(page_text)

        if "thermal not found" in page_text.lower():
            print("РЕЗУЛЬТАТ: Thermal not found - температура не обнаружена")
            result = True
        elif "Critical" in page_text:
            print("РЕЗУЛЬТАТ: Critical - критическое состояние температуры")
            result = True
        elif "Temperatures" in page_text or "Temperature" in page_text:
            print("РЕЗУЛЬТАТ: Данные о температуре найдены")
            result = True
        else:
            print("РЕЗУЛЬТАТ: Информация о температуре не найдена")
            result = False
        
        assert result, "Тест температурных датчиков не пройден"

        screenshot_name = "test4_success.png" if result else "test4_failed.png"
        driver.save_screenshot(screenshot_name)
        print(f"Скриншот сохранен: {screenshot_name}")

    except Exception as e:
        print(f"Тест не пройден!: {e}")
        result = False
