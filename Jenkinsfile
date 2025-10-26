pipeline {
    agent any

    environment {
        BMC_URL = 'https://localhost:2443'
        BMC_USERNAME = 'root'
        BMC_PASSWORD = '0penBmc'
        WORKSPACE_DIR = '/var/jenkins_home/workspace'
        QEMU_PID_FILE = '/tmp/qemu.pid'
    }

    stages {
        stage('Подготовка окружения') {
            steps {
                script {
                    sh '''
                        mkdir -p ${WORKSPACE}/artifacts/web_ui_tests
                        mkdir -p ${WORKSPACE}/artifacts/redfish_tests
                        mkdir -p ${WORKSPACE}/artifacts/load_tests
                        mkdir -p ${WORKSPACE}/artifacts/qemu_logs
                    '''
                }
            }
        }

        stage('Запуск QEMU с OpenBMC') {
            steps {
                script {
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
                            -net nic \
                            -net user,hostfwd=tcp::2443-:443,hostfwd=tcp::8082-:80,hostname=qemu \
                            > /tmp/qemu.log 2>&1 &
                        
                        QEMU_PID=$!
                        echo "QEMU запущен с PID: $QEMU_PID"
                        echo $QEMU_PID > /tmp/qemu.pid
                        sleep 5
                        
                        if ! ps -p $QEMU_PID > /dev/null; then
                            echo "ОШИБКА: QEMU не запустился!"
                            cat /tmp/qemu.log
                            exit 1
                        fi
                        
                        echo "Быстрая проверка OpenBMC (максимум 30 секунд)..."
                        timeout=30
                        elapsed=0
                        interval=3
                        while ! curl -k --silent --output /dev/null --connect-timeout 2 --max-time 3 https://localhost:2443/redfish/v1; do
                            sleep $interval
                            elapsed=$((elapsed+interval))
                            if [ $elapsed -ge $timeout ]; then
                                echo "OpenBMC не готов за $timeout секунд - тесты продолжат выполнение"
                                break
                            fi
                            printf "."
                        done
                        echo "\\nПродолжаем выполнение тестов"
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
                    sh '''
                        cd ${WORKSPACE}/web_ui_tests
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages
                        pytest web_ui_tests.py \
                            --html=${WORKSPACE}/artifacts/web_ui_tests/report.html \
                            --self-contained-html \
                            --junitxml=${WORKSPACE}/artifacts/web_ui_tests/junit.xml \
                            -v --tb=short
                    '''
                }
            }
            post {
                always {
                    sh '''
                        if [ -f ${WORKSPACE}/web_ui_tests/test1_success.png ] || [ -f ${WORKSPACE}/web_ui_tests/test3_failed.png ] || [ -f ${WORKSPACE}/web_ui_tests/test4_success.png ]; then
                            cp ${WORKSPACE}/web_ui_tests/test*.png ${WORKSPACE}/artifacts/web_ui_tests/ 2>/dev/null || true
                        fi
                    '''
                }
            }
        }

        stage('Redfish API Тесты') {
            steps {
                script {
                    sh '''
                        cd ${WORKSPACE}/redfish_api_tests
                        echo "Запуск Redfish API тестов..."
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages
                        pytest Redfish_API_tests.py \
                            --html=${WORKSPACE}/artifacts/redfish_tests/report.html \
                            --self-contained-html \
                            --junitxml=${WORKSPACE}/artifacts/redfish_tests/junit.xml \
                            -v --tb=short
                    '''
                }
            }
        }

        stage('Нагрузочное тестирование') {
            steps {
                script {
                    sh '''
                        cd ${WORKSPACE}/load_tests
                        echo "Запуск нагрузочного тестирования..."
                        pip3 install -r ${WORKSPACE}/requirements.txt --break-system-packages
                        locust -f Locust.py \
                            --headless \
                            --users 5 \
                            --spawn-rate 1 \
                            --run-time 30s \
                            --html=${WORKSPACE}/artifacts/load_tests/report.html \
                            --csv=${WORKSPACE}/artifacts/load_tests/stats
                    '''
                }
            }
        }

        stage('Сборка артефактов') {
            steps {
                script {
                    sh '''
                        echo "Сборка артефактов завершена"
                        ls -la ${WORKSPACE}/artifacts/
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
                        QEMU_PID=$(cat /tmp/qemu.pid)
                        kill $QEMU_PID 2>/dev/null || true
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
                reportFiles: '**/*.html',
                reportName: 'OpenBMC Test Report'
            ])
            
            junit 'artifacts/**/junit.xml'
        }
        
        failure {
            script {
                echo "=== Pipeline завершился с ошибкой ==="
            }
        }
    }
}