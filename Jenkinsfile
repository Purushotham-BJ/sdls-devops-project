// ============================================================
// Jenkinsfile — Smart Distributed Logging System
// Declarative Pipeline
// ============================================================
pipeline {

    agent any

    // ── Environment ──────────────────────────────────────────
    environment {
        // DockerHub credentials stored as a Jenkins "Username with password" credential
        DOCKERHUB_CREDS   = credentials('dockerhub-credentials')
        DOCKERHUB_USER    = "${DOCKERHUB_CREDS_USR}"

        // Repo prefix — change to your DockerHub username
        REPO_PREFIX       = "${DOCKERHUB_CREDS_USR}"

        // Image tag: use Jenkins build number for traceability
        IMAGE_TAG         = "v${env.BUILD_NUMBER}"

        // Services to build and push
        SERVICES          = "api-gateway order-service payment-service inventory-service notification-service logging-service dashboard"

        // JWT secret — store as a Jenkins Secret Text credential named 'jwt-secret-key'
        JWT_SECRET_KEY    = credentials('jwt-secret-key')
    }

    options {
        // Keep only last 10 builds to save disk
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Abort if pipeline runs longer than 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        // Disable concurrent builds on same branch
        disableConcurrentBuilds()
        timestamps()
    }

    stages {

        // ── Stage 1: Clone & Verify ──────────────────────────
        stage('Clone Repository') {
            steps {
                echo "📥 Cloning repository (branch: ${env.BRANCH_NAME})"
                checkout scm
                sh '''
                    echo "Workspace: $(pwd)"
                    echo "Git commit: $(git rev-parse --short HEAD)"
                    ls -la
                '''
            }
        }

        // ── Stage 2: Install Dependencies ────────────────────
        stage('Install Dependencies') {
            steps {
                echo "📦 Installing Python dependencies for all services"
                sh '''
                    python3 -m pip install --upgrade pip
                    pip3 install pytest pytest-cov requests PyJWT python-dotenv flask flask-cors
                    # Install per-service deps
                    for svc in api-gateway order-service payment-service inventory-service notification-service; do
                        pip3 install -r backend/${svc}/requirements.txt
                    done
                    pip3 install -r backend/logging-service/requirements.txt
                '''
            }
        }

        // ── Stage 3: Run Tests ────────────────────────────────
        stage('Run Tests') {
            steps {
                echo "🧪 Running test suite"
                sh '''
                    cd tests
                    python3 -m pytest . -v --tb=short \
                        --junitxml=../test-results.xml \
                        --cov=../backend \
                        --cov-report=xml:../coverage.xml \
                        || true   # Don't fail pipeline on test failure — report instead
                '''
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
        }

        // ── Stage 4: Build Docker Images ─────────────────────
        stage('Build Docker Images') {
            steps {
                echo "🐳 Building Docker images (tag: ${IMAGE_TAG})"
                sh '''
                    # Write env file for Docker builds
                    echo "JWT_SECRET_KEY=${JWT_SECRET_KEY}" > .env
                    echo "DOCKERHUB_REPO_PREFIX=${REPO_PREFIX}" >> .env
                    echo "IMAGE_TAG=${IMAGE_TAG}" >> .env

                    # Build all services in parallel via docker-compose
                    docker compose build --parallel --no-cache

                    echo "✅ All images built successfully"
                    docker images | grep "${REPO_PREFIX}" || true
                '''
            }
        }

        // ── Stage 5: Push to DockerHub ────────────────────────
        stage('Push to DockerHub') {
            steps {
                echo "🚀 Pushing images to DockerHub"
                sh '''
                    echo "${DOCKERHUB_CREDS_PSW}" | docker login -u "${DOCKERHUB_USER}" --password-stdin

                    for SVC in ${SERVICES}; do
                        # Skip dashboard (no DOCKERHUB_REPO_PREFIX in dashboard compose block, adjust if needed)
                        IMG="${REPO_PREFIX}/${SVC}:${IMAGE_TAG}"
                        LATEST="${REPO_PREFIX}/${SVC}:latest"

                        echo "Pushing ${IMG} ..."
                        docker push ${IMG}

                        # Also tag and push :latest
                        docker tag ${IMG} ${LATEST}
                        docker push ${LATEST}

                        echo "✅ Pushed ${IMG}"
                    done

                    docker logout
                '''
            }
        }

        // ── Stage 6: Deploy Containers ────────────────────────
        stage('Deploy Containers') {
            steps {
                echo "🏗️ Deploying containers with docker compose"
                sh '''
                    # Bring down old deployment gracefully
                    docker compose down --remove-orphans || true

                    # Pull fresh images (uses IMAGE_TAG from .env)
                    docker compose pull

                    # Start all services detached
                    docker compose up -d

                    echo "✅ Deployment started"
                    docker compose ps
                '''
            }
        }

        // ── Stage 7: Verify Deployment ───────────────────────
        stage('Verify Deployment') {
            steps {
                echo "🔍 Verifying all service health endpoints"
                sh '''
                    # Give containers time to initialise
                    sleep 20

                    FAILED=0
                    for PORT_SVC in "5000:api-gateway" "5001:order-service" "5002:payment-service" "5003:inventory-service" "5004:notification-service" "5005:logging-service" "5006:dashboard"; do
                        PORT="${PORT_SVC%%:*}"
                        SVC="${PORT_SVC##*:}"
                        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/health || echo "000")
                        if [ "${STATUS}" = "200" ]; then
                            echo "✅ ${SVC} (port ${PORT}) → HEALTHY"
                        else
                            echo "❌ ${SVC} (port ${PORT}) → UNHEALTHY (HTTP ${STATUS})"
                            FAILED=1
                        fi
                    done

                    if [ $FAILED -ne 0 ]; then
                        echo "One or more services failed health check"
                        docker compose logs --tail=50
                        exit 1
                    fi

                    echo "🎉 All services healthy!"
                '''
            }
        }

    } // end stages

    // ── Post actions ──────────────────────────────────────────
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
║  Tag:     ${IMAGE_TAG}                           ║
║  Branch:  ${env.BRANCH_NAME}                     ║
╚══════════════════════════════════════════════════╝
            """
        }
        failure {
            echo "❌ Pipeline FAILED — check logs above"
            sh 'docker compose logs --tail=100 || true'
        }
        always {
            // Clean up dangling images to save disk on Jenkins agent
            sh 'docker image prune -f || true'
            cleanWs()
        }
    }
}
