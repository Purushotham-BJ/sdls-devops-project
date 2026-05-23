pipeline {
    agent any

    environment {
        NAMESPACE = "sdls-dev"
    }

    stages {

        stage('Check Tools') {
            steps {
                sh 'docker --version'
                sh 'kubectl version --client'
                sh 'minikube status'
            }
        }

        stage('Build Images') {
            steps {

                dir('backend/api-gateway') {
                    sh 'docker build -t api-gateway:latest .'
                }

                dir('backend/order-service') {
                    sh 'docker build -t order-service:latest .'
                }

                dir('backend/payment-service') {
                    sh 'docker build -t payment-service:latest .'
                }

                dir('backend/inventory-service') {
                    sh 'docker build -t inventory-service:latest .'
                }

                dir('backend/notification-service') {
                    sh 'docker build -t notification-service:latest .'
                }

                dir('backend/logging-service') {
                    sh 'docker build -t logging-service:latest .'
                }

                dir('frontend/dashboard') {
                    sh 'docker build -t dashboard:latest .'
                }
            }
        }

        stage('Deploy Kubernetes') {
            steps {
                sh 'kubectl get pods -n sdls-dev'
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
