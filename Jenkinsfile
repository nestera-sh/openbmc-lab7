pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Prepare') {
            steps {

                sh 'rm -rf reports'
                sh 'mkdir -p reports'

                sh 'chmod +x scripts/*.sh'
            }
        }

        stage('Launch QEMU') {
            steps {
                sh 'bash ./scripts/start_qemu.sh'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/qemu/**/*', allowEmptyArchive: true
                }
            }
        }

        stage('OpenBMC automated tests (API)') {
            steps {
                sh 'bash ./scripts/run_api_tests.sh'
            }
            post {
                always {
                    junit testResults: 'reports/api/junit.xml', allowEmptyResults: true
                    archiveArtifacts artifacts: 'reports/api/**/*', allowEmptyArchive: true
                }
            }
        }

        stage('OpenBMC WebUI tests') {
            steps {
                sh 'bash ./scripts/run_webui_tests.sh'
            }
            post {
                always {
                    junit testResults: 'reports/webui/junit.xml', allowEmptyResults: true
                    archiveArtifacts artifacts: 'reports/webui/**/*', allowEmptyArchive: true
                }
            }
        }

        stage('OpenBMC load tests') {
            steps {
                sh 'bash ./scripts/run_load_tests.sh'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/load/**/*', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        always {
            sh '''
                if [ -f reports/qemu/qemu.pid ]; then
                    kill $(cat reports/qemu/qemu.pid) 2>/dev/null || true
                    rm -f reports/qemu/qemu.pid
                fi
            '''
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
        }
        cleanup {
            cleanWs()
        }
    }
}