from locust import HttpUser, task, between

class OpenBMCUser(HttpUser):

    host = "https://localhost:2443"
    wait_time = between(2, 5)

    def on_start(self):
        import time
        max_wait = 10  # Максимум 10 секунд ожидания
        wait_time = 0
        interval = 1
        
        print("Быстрая проверка готовности OpenBMC для нагрузочного тестирования...")
        while wait_time < max_wait:
            try:
                test_response = self.client.get("/redfish/v1/", verify=False, timeout=1)
                if test_response.status_code in [200, 401, 403]:
                    print(f"OpenBMC готов для нагрузочного тестирования (проверка заняла {wait_time} секунд)")
                    break
            except:
                pass
            
            print(f"Ожидание готовности OpenBMC... ({wait_time}/{max_wait} секунд)")
            time.sleep(interval)
            wait_time += interval
        
        if wait_time >= max_wait:
            print("OpenBMC не готов, завершение нагрузочного тестирования")
            self.environment.runner.quit()
            return
        
        try:
            auth_response = self.client.post(
                "/redfish/v1/SessionService/Sessions",
                json={"UserName": "root", "Password": "0penBmc"},
                verify=False,
                timeout=10
            )

            if auth_response.status_code in [200, 201]:
                token = auth_response.headers.get("X-Auth-Token")
                if token:
                    self.client.headers["X-Auth-Token"] = token
                    print(f"Успешная аутентификация, токен получен")
                else:
                    print("Ошибка: токен не получен")
            else:
                print(f"Ошибка аутентификации: {auth_response.status_code}")
        except Exception as e:
            print(f"Ошибка подключения к OpenBMC: {e}")

    @task(3)
    def get_system_info(self):
        with self.client.get(
                "/redfish/v1/Systems/system",
                verify=False,
                catch_response=True,
                name="Get System Info"
        ) as response:
            if response.status_code == 200:
                try:
                    system_data = response.json()
                    if "Id" in system_data and "Status" in system_data:
                        response.success()
                    else:
                        response.failure("Неполные данные в ответе")
                except ValueError:
                    response.failure("Невалидный JSON в ответе")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def get_power_state(self):
        with self.client.get(
                "/redfish/v1/Systems/system",
                verify=False,
                catch_response=True,
                name="Get Power State"
        ) as response:
            if response.status_code == 200:
                try:
                    system_data = response.json()
                    power_state = system_data.get("PowerState")
                    if power_state:
                        response.success()
                        print(f"PowerState: {power_state}")
                    else:
                        response.failure("PowerState отсутствует в ответе")
                except ValueError:
                    response.failure("Невалидный JSON в ответе")
            else:
                response.failure(f"HTTP {response.status_code}")
