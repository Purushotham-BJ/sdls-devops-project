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

                sh '''
                docker build -t api-gateway:latest -f backend/api-gateway/Dockerfile backend

                docker build -t order-service:latest -f backend/order-service/Dockerfile backend

                docker build -t payment-service:latest -f backend/payment-service/Dockerfile backend

                docker build -t inventory-service:latest -f backend/inventory-service/Dockerfile backend

                docker build -t notification-service:latest -f backend/notification-service/Dockerfile backend

                docker build -t logging-service:latest -f backend/logging-service/Dockerfile backend

                docker build -t dashboard:latest frontend/dashboard
                '''
            }
        }

        stage('Verify Kubernetes') {
            steps {
                sh 'kubectl get pods -n sdls-dev'
                sh 'kubectl get svc -n sdls-dev'
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
