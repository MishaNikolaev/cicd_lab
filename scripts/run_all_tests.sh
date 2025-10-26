#!/bin/bash

set -e

echo "=== Запуск всех тестов OpenBMC ==="

# Создаем директории для результатов
mkdir -p /var/jenkins_home/workspace/artifacts/web_ui_tests
mkdir -p /var/jenkins_home/workspace/artifacts/redfish_tests
mkdir -p /var/jenkins_home/workspace/artifacts/load_tests
mkdir -p /var/jenkins_home/workspace/artifacts/qemu_logs

# Устанавливаем права на скрипты
chmod +x /var/jenkins_home/workspace/scripts/*.sh

echo "1. Запуск QEMU с OpenBMC..."
/var/jenkins_home/workspace/scripts/start_qemu.sh

echo "2. Ожидание готовности OpenBMC..."
sleep 60

# Проверяем доступность OpenBMC
timeout=180
elapsed=0
while ! curl -k --silent --output /dev/null --connect-timeout 5 https://localhost:8443/redfish/v1; do
    sleep 10
    elapsed=$((elapsed+10))
    if [ $elapsed -ge $timeout ]; then
        echo "OpenBMC не поднялся за $timeout секунд"
        cat /tmp/qemu.log
        echo "Продолжаем выполнение тестов..."
        break
    fi
    printf "."
done
echo "\\nOpenBMC готов к работе или тесты продолжат выполнение"

echo "3. Запуск Web UI тестов..."
cd /var/jenkins_home/workspace/web_ui_tests
pip3 install -r /var/jenkins_home/workspace/requirements.txt --break-system-packages || true
pytest web_ui_tests.py \
    --html=/var/jenkins_home/workspace/artifacts/web_ui_tests/report.html \
    --self-contained-html \
    --junitxml=/var/jenkins_home/workspace/artifacts/web_ui_tests/junit.xml \
    -v || true

echo "4. Запуск Redfish API тестов..."
cd /var/jenkins_home/workspace/redfish_api_tests
pytest Redfish_API_tests.py \
    --html=/var/jenkins_home/workspace/artifacts/redfish_tests/report.html \
    --self-contained-html \
    --junitxml=/var/jenkins_home/workspace/artifacts/redfish_tests/junit.xml \
    -v || true

echo "5. Запуск нагрузочного тестирования..."
cd /var/jenkins_home/workspace/load_tests
locust -f Locust.py \
    --host=https://localhost:8443 \
    --users=10 \
    --spawn-rate=2 \
    --run-time=60s \
    --headless \
    --html=/var/jenkins_home/workspace/artifacts/load_tests/locust_report.html \
    --csv=/var/jenkins_home/workspace/artifacts/load_tests/locust_stats || true

echo "6. Копирование скриншотов..."
if [ -f /var/jenkins_home/workspace/web_ui_tests/*.png ]; then
    cp /var/jenkins_home/workspace/web_ui_tests/*.png /var/jenkins_home/workspace/artifacts/web_ui_tests/ || true
fi

echo "7. Копирование логов QEMU..."
if [ -f /tmp/qemu.log ]; then
    cp /tmp/qemu.log /var/jenkins_home/workspace/artifacts/qemu_logs/qemu_startup.log
fi

echo "8. Создание сводного отчета..."
cat > /var/jenkins_home/workspace/artifacts/test_summary.md << EOF
# Отчет о тестировании OpenBMC

- Начало: $(date '+%Y-%m-%d %H:%M:%S')
- Окончание: $(date '+%Y-%m-%d %H:%M:%S')

## Результаты тестов

### Web UI Тесты
- Отчет: [report.html](web_ui_tests/report.html)
- JUnit: [junit.xml](web_ui_tests/junit.xml)

### Redfish API Тесты  
- Отчет: [report.html](redfish_tests/report.html)
- JUnit: [junit.xml](redfish_tests/junit.xml)

### Нагрузочное тестирование
- Отчет: [locust_report.html](load_tests/locust_report.html)
- CSV данные: [locust_stats.csv](load_tests/locust_stats.csv)

### Логи QEMU
- [qemu_startup.log](qemu_logs/qemu_startup.log)

EOF

echo "=== Все тесты завершены ==="
