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
                        
                        echo "Ожидание полной загрузки OpenBMC..."
                        sleep 60
                        
                        echo "Проверка доступности OpenBMC..."
                        for i in {1..12}; do
                            echo "Попытка $i/12: проверка доступности OpenBMC..."
                            
                            # Проверяем HTTP порт
                            if curl -s --connect-timeout 5 --max-time 10 http://localhost:8082/ > /dev/null 2>&1; then
                                echo "✓ OpenBMC доступен на HTTP http://localhost:8082"
                                break
                            fi
                            
                            # Проверяем HTTPS порт
                            if curl -k -s --connect-timeout 5 --max-time 10 https://localhost:8443/redfish/v1/ > /dev/null 2>&1; then
                                echo "✓ OpenBMC доступен на HTTPS https://localhost:8443"
                                break
                            fi
                            
                            echo "OpenBMC еще не готов, ждем 15 секунд..."
                            sleep 15
                        done
                        
                        echo "Финальная проверка доступности OpenBMC..."
                        if curl -k -s --connect-timeout 5 --max-time 10 https://localhost:8443/redfish/v1/ > /dev/null 2>&1; then
                            echo "✓ OpenBMC готов к тестированию!"
                        else
                            echo "⚠ OpenBMC может быть еще не готов, но тесты продолжат выполнение"
                        fi
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
                        pip3 install -r ${WORKSPACE}/requirements.txt || true
                        
                        # Запуск демонстрационных Web UI тестов
                        pytest demo_tests.py \
                            --html=${WORKSPACE}/artifacts/web_ui_tests/report.html \
                            --self-contained-html \
                            --junitxml=${WORKSPACE}/artifacts/web_ui_tests/junit.xml \
                            -v
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
                        pip3 install -r ${WORKSPACE}/requirements.txt || true
                        
                        # Запуск демонстрационных тестов
                        pytest demo_tests.py \
                            --html=${WORKSPACE}/artifacts/redfish_tests/report.html \
                            --self-contained-html \
                            --junitxml=${WORKSPACE}/artifacts/redfish_tests/junit.xml \
                            -v
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
                        pip3 install -r ${WORKSPACE}/requirements.txt || true
                        
                        # Запуск демонстрационных Load тестов
                        locust -f demo_load_test.py \
                            --host=https://localhost:8443 \
                            --users=5 \
                            --spawn-rate=1 \
                            --run-time=30s \
                            --headless \
                            --html=${WORKSPACE}/artifacts/load_tests/locust_report.html \
                            --csv=${WORKSPACE}/artifacts/load_tests/locust_stats
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