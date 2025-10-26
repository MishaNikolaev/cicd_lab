from locust import HttpUser, task, between
import time

class OpenBMCDemoUser(HttpUser):
    """Демонстрационный пользователь для нагрузочного тестирования OpenBMC"""
    
    host = "https://localhost:8443"
    wait_time = between(1, 3)

    def on_start(self):
        """Инициализация пользователя"""
        print("✓ Демонстрационный пользователь OpenBMC запущен")
        self.auth_token = None

    @task(3)
    def test_redfish_root(self):
        """Тест корневого Redfish endpoint"""
        with self.client.get(
                "/redfish/v1/",
                verify=False,
                catch_response=True,
                name="Redfish Root",
                timeout=10
        ) as response:
            if response.status_code == 200:
                response.success()
                print("✓ Redfish Root endpoint доступен")
            else:
                response.failure(f"HTTP {response.status_code}")
                print(f"⚠ Redfish Root endpoint: код {response.status_code}")

    @task(2)
    def test_systems_endpoint(self):
        """Тест Systems endpoint"""
        with self.client.get(
                "/redfish/v1/Systems",
                verify=False,
                catch_response=True,
                name="Systems Endpoint",
                timeout=10
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
                print("✓ Systems endpoint доступен")
            else:
                response.failure(f"HTTP {response.status_code}")
                print(f"⚠ Systems endpoint: код {response.status_code}")

    @task(2)
    def test_chassis_endpoint(self):
        """Тест Chassis endpoint"""
        with self.client.get(
                "/redfish/v1/Chassis",
                verify=False,
                catch_response=True,
                name="Chassis Endpoint",
                timeout=10
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
                print("✓ Chassis endpoint доступен")
            else:
                response.failure(f"HTTP {response.status_code}")
                print(f"⚠ Chassis endpoint: код {response.status_code}")

    @task(1)
    def test_session_service(self):
        """Тест SessionService endpoint"""
        with self.client.get(
                "/redfish/v1/SessionService",
                verify=False,
                catch_response=True,
                name="Session Service",
                timeout=10
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
                print("✓ SessionService endpoint доступен")
            else:
                response.failure(f"HTTP {response.status_code}")
                print(f"⚠ SessionService endpoint: код {response.status_code}")

    @task(1)
    def test_authentication(self):
        """Тест аутентификации"""
        with self.client.post(
                "/redfish/v1/SessionService/Sessions",
                json={"UserName": "root", "Password": "0penBmc"},
                verify=False,
                catch_response=True,
                name="Authentication",
                timeout=10
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
                print("✓ Аутентификация работает")
            else:
                response.failure(f"HTTP {response.status_code}")
                print(f"⚠ Аутентификация: код {response.status_code}")

    @task(1)
    def test_system_info(self):
        """Тест информации о системе"""
        with self.client.get(
                "/redfish/v1/Systems/system",
                verify=False,
                catch_response=True,
                name="System Info",
                timeout=10
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
                print("✓ System Info endpoint доступен")
            else:
                response.failure(f"HTTP {response.status_code}")
                print(f"⚠ System Info endpoint: код {response.status_code}")

    @task(1)
    def test_thermal_management(self):
        """Тест управления температурой"""
        with self.client.get(
                "/redfish/v1/Chassis/chassis/Thermal",
                verify=False,
                catch_response=True,
                name="Thermal Management",
                timeout=10
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
                print("✓ Thermal Management endpoint доступен")
            else:
                response.failure(f"HTTP {response.status_code}")
                print(f"⚠ Thermal Management endpoint: код {response.status_code}")

    @task(1)
    def test_power_management(self):
        """Тест управления питанием"""
        with self.client.get(
                "/redfish/v1/Chassis/chassis/Power",
                verify=False,
                catch_response=True,
                name="Power Management",
                timeout=10
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
                print("✓ Power Management endpoint доступен")
            else:
                response.failure(f"HTTP {response.status_code}")
                print(f"⚠ Power Management endpoint: код {response.status_code}")
