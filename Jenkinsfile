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
                    
                    echo "Окружение подготовлено"
                }
            }
        }

        stage('Запуск QEMU с OpenBMC') {
            steps {
                script {
                    echo "=== Запуск QEMU с OpenBMC ==="
                    
                    sh '''
                        pkill qemu-system-arm || true
                        rm -f /tmp/qemu.pid
                        sleep 2
                        
                        cd ${WORKSPACE}/romulus
                        
                        if [ ! -f "obmc-phosphor-image-romulus-20250902012112.static.mtd" ]; then
                            echo "ОШИБКА: MTD файл не найден!"
                            exit 1
                        fi
                        
                        echo "MTD файл найден: obmc-phosphor-image-romulus-20250902012112.static.mtd"
                        
                        echo "Запуск QEMU..."
                        nohup qemu-system-arm \
                            -M romulus-bmc \
                            -nographic \
                            -drive file=obmc-phosphor-image-romulus-20250902012112.static.mtd,format=raw,if=mtd \
                            -net user,hostfwd=tcp::8443-:443,hostfwd=tcp::8082-:80 \
                            > /tmp/qemu.log 2>&1 &
                        
                        QEMU_PID=$!
                        echo "QEMU запущен с PID: $QEMU_PID"
                        echo "$QEMU_PID" > /tmp/qemu.pid
                        
                        sleep 5
                        if ! ps -p $QEMU_PID > /dev/null; then
                            echo "QEMU не запущен!"
                            cat /tmp/qemu.log
                            exit 1
                        fi
                        
                        echo "Ожидание готовности OpenBMC..."
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
                        
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages || true
                        
                        pytest web_ui_tests.py \
                            --html=${WORKSPACE}/artifacts/web_ui_tests/report.html \
                            --self-contained-html \
                            --junitxml=${WORKSPACE}/artifacts/web_ui_tests/junit.xml \
                            -v --tb=short || true
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
                        
                        echo "Проверка готовности OpenBMC для Redfish API..."
                        
                        # Быстрая проверка - если не готов за 10 секунд, продолжаем
                        if curl -k -s --connect-timeout 2 --max-time 3 https://localhost:8443/redfish/v1/ > /dev/null 2>&1; then
                            echo "✅ Redfish API готов!"
                        else
                            echo "⚠ Redfish API не готов, но тесты продолжат выполнение"
                            echo "Это нормально для демонстрации CI/CD pipeline"
                        fi
                        
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages || true
                        
                        pytest Redfish_API_tests.py \
                            --html=${WORKSPACE}/artifacts/redfish_tests/report.html \
                            --self-contained-html \
                            --junitxml=${WORKSPACE}/artifacts/redfish_tests/junit.xml \
                            -v --tb=short --timeout=30 || true
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
                        
                        echo "Ожидание готовности OpenBMC для нагрузочного тестирования..."
                        MAX_WAIT=120
                        WAIT_TIME=0
                        INTERVAL=5
                        
                        while [ $WAIT_TIME -lt $MAX_WAIT ]; do
                            if curl -k -s --connect-timeout 5 --max-time 10 https://localhost:8443/redfish/v1/ > /dev/null 2>&1; then
                                echo "OpenBMC готов для нагрузочного тестирования"
                                break
                            fi
                            
                            echo "Ожидание готовности OpenBMC... ($WAIT_TIME/$MAX_WAIT секунд)"
                            sleep $INTERVAL
                            WAIT_TIME=$((WAIT_TIME + INTERVAL))
                        done
                        
                        if [ $WAIT_TIME -ge $MAX_WAIT ]; then
                            echo "OpenBMC не готов, но тесты продолжат выполнение"
                        fi
                        
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages || true
                        
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
                        cat > ${WORKSPACE}/artifacts/test_summary.md << EOF

- Начало: $(date -d @${BUILD_TIMESTAMP} '+%Y-%m-%d %H:%M:%S')
- Окончание: $(date '+%Y-%m-%d %H:%M:%S')

- Отчет: [report.html](web_ui_tests/report.html)
- JUnit: [junit.xml](web_ui_tests/junit.xml)

- Отчет: [report.html](redfish_tests/report.html)
- JUnit: [junit.xml](redfish_tests/junit.xml)

- Отчет: [locust_report.html](load_tests/locust_report.html)
- CSV данные: [locust_stats.csv](load_tests/locust_stats.csv)

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
                    if [ -f /tmp/qemu.pid ]; then
                        kill $(cat /tmp/qemu.pid) || true
                        rm -f /tmp/qemu.pid
                    fi
                    pkill qemu-system-arm || true
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