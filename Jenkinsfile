pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Launch QEMU') {
            steps {
                echo 'Launching OpenBMC QEMU...'
            }
        }

        stage('OpenBMC automated tests') {
            steps {
                echo 'Running OpenBMC automated tests...'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/api/**/*',
                                     allowEmptyArchive: true
                }
            }
        }

        stage('OpenBMC WebUI tests') {
            steps {
                echo 'Running OpenBMC WebUI tests...'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/webui/**/*',
                                     allowEmptyArchive: true
                }
            }
        }

        stage('OpenBMC load tests') {
            steps {
                echo 'Running OpenBMC load tests...'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/load/**/*',
                                     allowEmptyArchive: true
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**/*',
                             allowEmptyArchive: true
        }
    }
}
