pipeline {
    agent any

    stages {

        stage('Check Tools') {
            steps {
                sh 'docker --version'
                sh 'kubectl version --client'

                sh '''
                for i in {1..20}; do
                  kubectl get nodes && exit 0
                  echo "Waiting for Kubernetes..."
                  sleep 10
                done
                exit 1
                '''
            }
        }

        stage('Build Images') {
            steps {
                sh 'echo Building images...'
            }
        }

        stage('Verify Kubernetes') {
            steps {
                sh 'kubectl get pods -A'
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished'
        }

        success {
            echo 'Pipeline SUCCESS'
        }

        failure {
            echo 'Pipeline FAILED'
        }
    }
}
