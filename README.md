# Smart Distributed Logging & Failure Analysis System
## Industry-Level DevOps Upgrade — Complete Guide

---

## Project Overview

A production-ready microservices system featuring JWT-authenticated API gateway,
Dockerised services, Jenkins CI/CD pipeline, centralised logging, and DockerHub integration.

---

## Final Project Structure

```
smart-distributed-logging-system/
├── .env.example                  ← Environment variable template
├── .env                          ← Local secrets (never commit!)
├── .gitignore
├── docker-compose.yml            ← Production-ready multi-service compose
├── Jenkinsfile                   ← Declarative CI/CD pipeline
├── requirements.txt
│
├── backend/
│   ├── shared/
│   │   ├── constants.py          ← All config read from env vars
│   │   ├── utils.py              ← send_log() helper
│   │   ├── log_format.py
│   │   └── trace_generator.py
│   │
│   ├── api-gateway/              ← Port 5000
│   │   ├── app.py                ← Flask app + env/logging setup
│   │   ├── auth.py               ← JWT: /login, generate_token, jwt_required
│   │   ├── routes.py             ← All routes — JWT-protected
│   │   ├── Dockerfile            ← Multi-stage, non-root, healthcheck
│   │   ├── requirements.txt      ← Includes PyJWT
│   │   └── .dockerignore
│   │
│   ├── order-service/            ← Port 5001
│   ├── payment-service/          ← Port 5002
│   ├── inventory-service/        ← Port 5003
│   ├── notification-service/     ← Port 5004
│   ├── logging-service/          ← Port 5005
│   └── database/
│       └── mongo-init.js
│
├── frontend/
│   └── dashboard/                ← Port 5006
│
├── tests/
│   ├── conftest.py
│   ├── test_jwt_auth.py          ← 12 pytest tests for JWT
│   └── test_health_checks.py     ← Route protection + health tests
│
└── scripts/
    ├── deploy.sh                 ← Local deployment helper
    └── test_api.sh               ← curl-based API smoke tests
```

---

## What Was Added / Changed

| Area | Before | After |
|------|--------|-------|
| Authentication | None | JWT via `auth.py` — `POST /login`, `@jwt_required` decorator |
| API routes | All public | All `/api/*` require `Authorization: Bearer <token>` |
| Secrets | Hardcoded in `constants.py` | All values from `.env` via `python-dotenv` |
| Dockerfiles | Basic single-stage | Multi-stage, non-root user, HEALTHCHECK |
| docker-compose | No health checks, no restart | `restart: always`, `healthcheck`, `depends_on: condition: service_healthy` |
| Logging | Basic | Structured ISO timestamps, configurable LOG_LEVEL |
| CI/CD | None | 7-stage Jenkins declarative pipeline with DockerHub push |
| Tests | None | 18 pytest tests covering JWT, login, route protection |
| Docker images | Local only | Tagged `repo/service:vBUILD_NUM` and `:latest` |

---

## Environment Variables Reference

Copy `.env.example` → `.env` and fill in your values:

```bash
cp .env.example .env
# Edit .env — minimum required changes:
#   JWT_SECRET_KEY=<strong-random-secret>
#   DOCKERHUB_USERNAME=<your-dockerhub-username>
```

| Variable | Purpose | Default |
|----------|---------|---------|
| `JWT_SECRET_KEY` | Signs JWT tokens — keep secret! | `CHANGE_ME_...` |
| `JWT_ALGORITHM` | Token signing algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `MONGO_URI` | MongoDB connection string | `mongodb://mongodb:27017` |
| `LOGGING_SERVICE_URL` | Where services send logs | `http://logging-service:5005` |
| `ORDER_SERVICE_URL` | Internal order service URL | `http://order-service:5001` |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `FLASK_DEBUG` | Enable debug mode | `0` |
| `DOCKERHUB_REPO_PREFIX` | DockerHub username/org | `yourdockerhubusername` |
| `IMAGE_TAG` | Docker image tag | `latest` |

---

## How to Run Locally

### Prerequisites
- Docker Desktop (or Docker Engine + Compose v2)
- Python 3.11+ (for running tests without Docker)

### Option A — Full Docker Stack (recommended)

```bash
# 1. Clone and set up environment
git clone <your-repo-url>
cd smart-distributed-logging-system
cp .env.example .env
# Edit .env: set JWT_SECRET_KEY at minimum

# 2. Start everything
./scripts/deploy.sh up
# OR manually:
docker compose up -d --build

# 3. Check status
./scripts/deploy.sh status

# 4. View logs
./scripts/deploy.sh logs            # all services
./scripts/deploy.sh logs api-gateway # single service
```

### Option B — Run tests only

```bash
pip install pytest PyJWT flask flask-cors python-dotenv requests
pytest tests/ -v
```

---

## Authentication API

### POST /login — Get a JWT token

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {"username": "admin", "role": "admin"}
}
```

Demo users (change in production — add a real user DB):

| Username | Password | Role |
|----------|----------|------|
| `admin`  | `admin123` | admin |
| `user`   | `user123`  | viewer |

### Using the token

```bash
# Save the token
TOKEN=$(curl -s -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .token)

# Place an order
curl -X POST http://localhost:5000/api/order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"product_id": "PROD-001", "quantity": 2, "customer_id": "CUST-0001"}'

# Check inventory
curl -X GET http://localhost:5000/api/inventory \
  -H "Authorization: Bearer $TOKEN"

# Bulk simulate (5 orders)
curl -X POST http://localhost:5000/api/simulate/bulk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"count": 5}'
```

### Run the full API smoke test

```bash
./scripts/test_api.sh
```

---

## Jenkins CI/CD Setup

### 1. Install Jenkins plugins required
- Docker Pipeline
- GitHub Integration
- Credentials Binding
- JUnit (for test reports)

### 2. Add Jenkins credentials

| Credential ID | Type | Value |
|---------------|------|-------|
| `dockerhub-credentials` | Username with Password | Your DockerHub login |
| `jwt-secret-key` | Secret Text | Strong random string |

```
Jenkins → Manage Jenkins → Credentials → System → Global → Add Credential
```

### 3. Create Pipeline Job

```
New Item → Pipeline
  → Pipeline script from SCM
  → SCM: Git
  → Repository URL: <your-github-repo-url>
  → Branch: */main
  → Script Path: Jenkinsfile
```

### 4. Configure GitHub webhook (auto-trigger on push)

```
GitHub Repo → Settings → Webhooks → Add webhook
  → Payload URL: http://<jenkins-host>:8080/github-webhook/
  → Content type: application/json
  → Events: Just the push event
```

### Pipeline stages

```
Clone → Install Deps → Run Tests → Build Images → Push DockerHub → Deploy → Verify
```

DockerHub images are tagged as:
```
yourdockerhubusername/api-gateway:v42          ← build number
yourdockerhubusername/api-gateway:latest       ← always latest
```

---

## Docker Image Architecture

Each service uses a **multi-stage build**:

```dockerfile
# Stage 1: install deps (builder)
FROM python:3.11-slim AS builder
RUN pip install --prefix=/install/deps ...

# Stage 2: lean runtime (no build tools)
FROM python:3.11-slim
COPY --from=builder /install/deps /usr/local
# Runs as non-root user 'appuser'
```

Benefits:
- Final image ~100MB smaller (no pip, build tools)
- Non-root execution (security)
- HEALTHCHECK built into image
- `restart: always` via compose

---

## Troubleshooting

### Services not starting
```bash
docker compose logs --tail=50 <service-name>
docker compose ps
```

### JWT token errors
- `401 Token has expired` → re-login to get a fresh token
- `401 Invalid token` → check you're sending `Authorization: Bearer <token>` (not just the token)
- `401 Authorization header missing` → add the header

### MongoDB connection issues
```bash
docker compose logs mongodb
# Check it's healthy before other services start
docker inspect sdls-mongodb | grep -A5 Health
```

### Jenkins: Docker permission denied
```bash
# On Jenkins host — add jenkins user to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### Port conflicts
```bash
# Check what's using a port
lsof -i :5000
# Change ports in .env: API_GATEWAY_PORT=5010
```
