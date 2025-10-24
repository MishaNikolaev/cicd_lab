pipeline {
    agent {
        docker {
            image 'python:3.9-slim'
            args '--privileged -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        BMC_URL = 'https://qemu-openbmc:2443'
        BMC_USERNAME = 'root'
        BMC_PASSWORD = '0penBmc'
    }

    stages {
        stage('Install Tools') {
            steps {
                sh '''
                    apt-get update
                    apt-get install -y curl docker.io
                    pip install docker-compose

                    echo "Python: $(python --version)"
                    echo "Pip: $(pip --version)"
                    echo "Docker: $(docker --version)"
                    echo "Docker Compose: $(docker-compose --version)"
                '''
            }
        }

        stage('Start Infrastructure') {
            steps {
                sh '''
                    docker-compose up -d qemu-openbmc
                    sleep 30
                '''
            }
        }

        stage('Simple Test') {
            steps {
                sh '''
                    curl -k -u root:0penBmc https://qemu-openbmc:2443/redfish/v1/ || echo "BMC not ready yet"
                '''
            }
        }
    }
}