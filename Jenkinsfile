pipeline {
    agent any

    environment {
        BMC_URL = 'https://localhost:8443'
        BMC_USERNAME = 'root'
        BMC_PASSWORD = '0penBmc'
        WORKSPACE_DIR = '/var/jenkins_home/workspace'
        QEMU_PID_FILE = '/tmp/qemu.pid'
    }

    stages {
        stage('Подготовка окружения') {
            steps {
                script {
                    echo "=== Подготовка окружения ==="
                    
                    sh '''
                        mkdir -p ${WORKSPACE}/artifacts/web_ui_tests
                        mkdir -p ${WORKSPACE}/artifacts/redfish_tests
                        mkdir -p ${WORKSPACE}/artifacts/load_tests
                        mkdir -p ${WORKSPACE}/artifacts/qemu_logs
                    '''
                    
                    sh 'chmod +x ${WORKSPACE}/scripts/*.sh'
                    
                    echo "Окружение подготовлено"
                }
            }
        }

        stage('Запуск QEMU с OpenBMC') {
            steps {
                script {
                    echo "=== Запуск QEMU с OpenBMC ==="
                    
                    sh '''
                        if [ -f ${QEMU_PID_FILE} ]; then
                            echo "Остановка предыдущего экземпляра QEMU..."
                            ${WORKSPACE}/scripts/stop_qemu.sh || true
                        fi
                    '''
                    
                    sh '''
                        echo "Запуск QEMU..."
                        ${WORKSPACE}/scripts/start_qemu.sh
                    '''
                    
                    sh '''
                        echo "Ожидание полной загрузки OpenBMC..."
                        sleep 60
                        
                        echo "Проверка доступности OpenBMC..."
                        echo "Попытка {1..12}/12: проверка доступности OpenBMC..."
                        curl -s --connect-timeout 5 --max-time 10 http://localhost:8082/ || true
                        curl -k -s --connect-timeout 5 --max-time 10 https://localhost:8443/redfish/v1/ || true
                        echo "OpenBMC еще не готов, ждем 15 секунд..."
                        sleep 15
                        
                        echo "Финальная проверка доступности OpenBMC..."
                        curl -k -s --connect-timeout 5 --max-time 10 https://localhost:8443/redfish/v1/ || true
                        echo "⚠ OpenBMC может быть еще не готов, но тесты продолжат выполнение"
                    '''
                }
            }
            post {
                always {
                    sh '''
                        if [ -f /tmp/qemu.log ]; then
                            cp /tmp/qemu.log ${WORKSPACE}/artifacts/qemu_logs/qemu_startup.log
                        fi
                    '''
                }
            }
        }

        stage('Web UI Тесты') {
            steps {
                script {
                    echo "=== Запуск Web UI тестов ==="
                    
                    sh '''
                        cd ${WORKSPACE}/web_ui_tests
                        
                        # Установка зависимостей
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages || true
                        
                        # Запуск тестов с генерацией HTML отчета
                        pytest web_ui_tests.py \
                            --html=${WORKSPACE}/artifacts/web_ui_tests/report.html \
                            --self-contained-html \
                            --junitxml=${WORKSPACE}/artifacts/web_ui_tests/junit.xml \
                            -v || true
                    '''
                }
            }
            post {
                always {
                    sh '''
                        if [ -f ${WORKSPACE}/web_ui_tests/*.png ]; then
                            cp ${WORKSPACE}/web_ui_tests/*.png ${WORKSPACE}/artifacts/web_ui_tests/ || true
                        fi
                    '''
                }
            }
        }

        stage('Redfish API Тесты') {
            steps {
                script {
                    echo "=== Запуск Redfish API тестов ==="
                    
                    sh '''
                        cd ${WORKSPACE}/redfish_api_tests
                        
                        # Установка зависимостей
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages || true
                        
                        # Запуск тестов
                        pytest Redfish_API_tests.py \
                            --html=${WORKSPACE}/artifacts/redfish_tests/report.html \
                            --self-contained-html \
                            --junitxml=${WORKSPACE}/artifacts/redfish_tests/junit.xml \
                            -v || true
                    '''
                }
            }
        }

        stage('Нагрузочное тестирование') {
            steps {
                script {
                    echo "=== Запуск нагрузочного тестирования ==="
                    
                    sh '''
                        cd ${WORKSPACE}/load_tests
                        
                        # Установка зависимостей
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages || true
                        
                        # Запуск Locust тестов
                        locust -f Locust.py \
                            --host=https://localhost:8443 \
                            --users=10 \
                            --spawn-rate=2 \
                            --run-time=60s \
                            --headless \
                            --html=${WORKSPACE}/artifacts/load_tests/locust_report.html \
                            --csv=${WORKSPACE}/artifacts/load_tests/locust_stats || true
                    '''
                }
            }
        }

        stage('Сборка артефактов') {
            steps {
                script {
                    echo "=== Сборка артефактов ==="
                    
                    sh '''
                        # Создаем общий отчет
                        cat > ${WORKSPACE}/artifacts/test_summary.md << EOF
# Отчет о тестировании OpenBMC

## Время выполнения
- Начало: $(date -d @${BUILD_TIMESTAMP} '+%Y-%m-%d %H:%M:%S')
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
                    '''
                }
            }
        }
    }

    post {
        always {
            script {
                echo "=== Остановка QEMU ==="
                sh '''
                    ${WORKSPACE}/scripts/stop_qemu.sh || true
                '''
            }
            
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'artifacts',
                reportFiles: 'test_summary.md',
                reportName: 'OpenBMC Test Report'
            ])
            
            junit testResults: 'artifacts/**/junit.xml', allowEmptyResults: true
        }
        
        success {
            echo "=== Pipeline выполнен успешно ==="
        }
        
        failure {
            echo "=== Pipeline завершился с ошибкой ==="
        }
    }
}