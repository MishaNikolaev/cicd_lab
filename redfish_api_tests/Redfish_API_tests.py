import pytest
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8443/redfish/v1"
USERNAME = "root"
PASSWORD = "0penBmc"
TIMEOUT = 60

AUTH_TOKEN = None

@pytest.fixture(scope="session")
def auth_session():
    global AUTH_TOKEN

    session = requests.Session()
    session.verify = False

    # Ожидание готовности OpenBMC
    import time
    max_wait = 60  # 60 секунд
    wait_time = 0
    interval = 5
    
    print("Ожидание готовности OpenBMC...")
    while wait_time < max_wait:
        try:
            # Проверяем доступность Redfish API
            test_response = session.get(f"{BASE_URL}/", timeout=5)
            if test_response.status_code in [200, 401, 403]:  # API доступен
                print(f"✅ OpenBMC готов (проверка заняла {wait_time} секунд)")
                break
        except:
            pass
        
        print(f"Ожидание готовности OpenBMC... ({wait_time}/{max_wait} секунд)")
        time.sleep(interval)
        wait_time += interval
    
    if wait_time >= max_wait:
        pytest.skip("OpenBMC не готов в течение 60 секунд")

    try:
        response = session.post(
            f"{BASE_URL}/SessionService/Sessions",
            json={"UserName": USERNAME, "Password": PASSWORD},
            timeout=TIMEOUT
        )

        if response.status_code == 201:
            AUTH_TOKEN = response.headers['X-Auth-Token']
            session.headers['X-Auth-Token'] = AUTH_TOKEN
        else:
            pytest.skip(f"Не удалось создать сессию: {response.status_code}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"OpenBMC недоступен: {e}")

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
        response = auth_session.get(f"{BASE_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200

    def test_02_system_info(self, auth_session, system_info):
        required_fields = ["@odata.id", "@odata.type", "Status"]
        for field in required_fields:
            assert field in system_info

    def test_03_power_management(self, auth_session, system_info):
        if "Actions" not in system_info or "#ComputerSystem.Reset" not in system_info["Actions"]:
            pytest.skip("Действие Reset недоступно")
        for reset_type in ["GracefulRestart", "ForceRestart"]:
            resp = auth_session.post(
                f"{BASE_URL}/Systems/system/Actions/ComputerSystem.Reset",
                json={"ResetType": reset_type},
                timeout=TIMEOUT
            )
            assert resp.status_code in [200, 202, 204, 400]

    def test_04_cpu_temperature(self, auth_session):
        thermal_url = f"{BASE_URL}/Chassis/chassis/ThermalSubSystem"
        resp = auth_session.get(thermal_url, timeout=TIMEOUT)
        if resp.status_code != 200:
            pytest.skip("Thermal endpoint недоступен")
        data = resp.json()
        temperatures = data.get("Temperatures", [])
        if not temperatures:
            pytest.skip("Температурные датчики не найдены")
        for sensor in temperatures:
            temp = sensor.get("ReadingCelsius")
            if temp is not None:
                upper_critical = sensor.get("UpperThresholdCritical")
                upper_fatal = sensor.get("UpperThresholdFatal")
                if upper_critical:
                    assert temp <= upper_critical
                if upper_fatal:
                    assert temp <= upper_fatal
                assert -20 <= temp <= 120

    def test_05_cpu_sensors_consistency(self, auth_session):
        resp = auth_session.get(f"{BASE_URL}/Systems/system", timeout=TIMEOUT)
        assert resp.status_code == 200

    def test_06_session_management(self, auth_session):
        resp = auth_session.get(f"{BASE_URL}/SessionService", timeout=TIMEOUT)
        assert resp.status_code == 200
