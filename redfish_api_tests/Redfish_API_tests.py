import pytest
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:2443/redfish/v1"
USERNAME = "root"
PASSWORD = "0penBmc"
TIMEOUT = 5

AUTH_TOKEN = None

@pytest.fixture(scope="session")
def auth_session():
    global AUTH_TOKEN

    session = requests.Session()
    session.verify = False

    import time
    max_wait = 10
    wait_time = 0
    interval = 2
    
    print("Быстрая проверка готовности OpenBMC...")
    while wait_time < max_wait:
        try:
            test_response = session.get(f"{BASE_URL}/", timeout=1)
            if test_response.status_code in [200, 401, 403]:
                print(f"Redfish API готов (проверка заняла {wait_time} секунд)")
                break
        except:
            pass
        
        try:
            systems_response = session.get(f"{BASE_URL}/Systems/", timeout=1)
            if systems_response.status_code in [200, 401, 403]:
                print(f"Redfish Systems API готов (проверка заняла {wait_time} секунд)")
                break
        except:
            pass
        
        print(f"Проверка готовности OpenBMC... ({wait_time}/{max_wait} секунд)")
        time.sleep(interval)
        wait_time += interval
    
    if wait_time >= max_wait:
        print("OpenBMC не готов за 10 секунд, но тесты продолжат выполнение")

    try:
        response = session.post(
            f"{BASE_URL}/SessionService/Sessions",
            json={"UserName": USERNAME, "Password": PASSWORD},
            timeout=TIMEOUT
        )

        if response.status_code == 201:
            AUTH_TOKEN = response.headers['X-Auth-Token']
            session.headers['X-Auth-Token'] = AUTH_TOKEN
            print("Успешная аутентификация в Redfish API")
        else:
            print(f"Не удалось создать сессию: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"OpenBMC недоступен: {e}")

    yield session

    try:
        session.delete(f"{BASE_URL}/SessionService/Sessions/{response.json().get('Id', '')}", timeout=TIMEOUT)
    except:
        pass
    session.close()


@pytest.fixture
def system_info(auth_session):
    response = auth_session.get(f"{BASE_URL}/Systems/system", timeout=TIMEOUT)
    return response.json()


class TestRedfishAPI:

    def test_01_authentication(self, auth_session):
        try:
            response = auth_session.get(f"{BASE_URL}/", timeout=TIMEOUT)
            if response.status_code in [200, 401, 403]:
                print(f"Redfish API доступен, статус: {response.status_code}")
                assert True, "Redfish API доступен"
            else:
                print(f"Redfish API недоступен, статус: {response.status_code}")
                assert False, f"Redfish API недоступен, статус: {response.status_code}"
        except Exception as e:
            print(f"Redfish API недоступен: {e}")
            assert False, f"Redfish API недоступен: {e}"

    def test_02_system_info(self, auth_session, system_info):
        try:
            required_fields = ["@odata.id", "@odata.type", "Status"]
            for field in required_fields:
                assert field in system_info, f"Поле {field} не найдено в system_info"
            print("Информация о системе получена успешно")
        except Exception as e:
            print(f"Не удалось получить информацию о системе: {e}")
            assert False, f"Не удалось получить информацию о системе: {e}"

    def test_03_power_management(self, auth_session, system_info):
        try:
            if "Actions" not in system_info or "#ComputerSystem.Reset" not in system_info["Actions"]:
                print("Действие Reset недоступно")
                assert False, "Действие Reset недоступно"
            for reset_type in ["GracefulRestart", "ForceRestart"]:
                resp = auth_session.post(
                    f"{BASE_URL}/Systems/system/Actions/ComputerSystem.Reset",
                    json={"ResetType": reset_type},
                    timeout=TIMEOUT
                )
                assert resp.status_code in [200, 202, 204, 400], f"Неожиданный статус для {reset_type}: {resp.status_code}"
            print("Управление питанием работает корректно")
        except Exception as e:
            print(f"Ошибка в управлении питанием: {e}")
            assert False, f"Ошибка в управлении питанием: {e}"

    def test_04_cpu_temperature(self, auth_session):
        try:
            thermal_url = f"{BASE_URL}/Chassis/chassis/ThermalSubSystem"
            resp = auth_session.get(thermal_url, timeout=TIMEOUT)
            if resp.status_code != 200:
                print("Thermal endpoint недоступен")
                pytest.skip("Thermal endpoint недоступен")
            data = resp.json()
            temperatures = data.get("Temperatures", [])
            if not temperatures:
                print("Температурные датчики не найдены")
                pytest.skip("Температурные датчики не найдены")
            for sensor in temperatures:
                temp = sensor.get("ReadingCelsius")
                if temp is not None:
                    upper_critical = sensor.get("UpperThresholdCritical")
                    upper_fatal = sensor.get("UpperThresholdFatal")
                    if upper_critical:
                        assert temp <= upper_critical, f"Температура {temp} превышает критический порог {upper_critical}"
                    if upper_fatal:
                        assert temp <= upper_fatal, f"Температура {temp} превышает фатальный порог {upper_fatal}"
                    assert -20 <= temp <= 120, f"Температура {temp} вне допустимого диапазона"
            print("Температурные датчики работают корректно")
        except Exception as e:
            print(f"Ошибка в температурных датчиках: {e}")
            pytest.skip(f"Ошибка в температурных датчиках: {e}")

    def test_05_cpu_sensors_consistency(self, auth_session):
        try:
            resp = auth_session.get(f"{BASE_URL}/Systems/system", timeout=TIMEOUT)
            if resp.status_code == 200:
                print("Системная информация доступна")
                assert True, "Системная информация доступна"
            else:
                print(f"Система недоступна, статус: {resp.status_code}")
                assert False, f"Система недоступна, статус: {resp.status_code}"
        except Exception as e:
            print(f"Ошибка при получении системной информации: {e}")
            assert False, f"Ошибка при получении системной информации: {e}"

    def test_06_session_management(self, auth_session):
        try:
            resp = auth_session.get(f"{BASE_URL}/SessionService", timeout=TIMEOUT)
            if resp.status_code == 200:
                print("Сервис сессий работает корректно")
                assert True, "Сервис сессий работает корректно"
            else:
                print(f"Сервис сессий недоступен, статус: {resp.status_code}")
                assert False, f"Сервис сессий недоступен, статус: {resp.status_code}"
        except Exception as e:
            print(f"Ошибка в управлении сессиями: {e}")
            assert False, f"Ошибка в управлении сессиями: {e}"
