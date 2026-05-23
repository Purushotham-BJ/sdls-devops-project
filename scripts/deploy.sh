#!/usr/bin/env bash
# ============================================================
# scripts/deploy.sh  —  Full local deployment script
# Usage: ./scripts/deploy.sh [up|down|restart|logs|status]
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Load .env if it exists
if [[ -f .env ]]; then
    set -a; source .env; set +a
fi

IMAGE_TAG="${IMAGE_TAG:-latest}"
COMPOSE="docker compose"

usage() {
    echo "Usage: $0 [up|down|restart|logs|status|build|test]"
    exit 1
}

cmd="${1:-up}"

case "$cmd" in

  up)
    echo "🚀 Starting all services (IMAGE_TAG=${IMAGE_TAG})..."
    $COMPOSE up -d --build
    echo ""
    echo "⏳ Waiting for services to become healthy..."
    sleep 15
    $COMPOSE ps
    echo ""
    echo "✅ Stack is up! Access:"
    echo "   Dashboard  → http://localhost:5006"
    echo "   API Gateway→ http://localhost:5000"
    echo "   Docs       → http://localhost:5000/health"
    ;;

  down)
    echo "🛑 Stopping all services..."
    $COMPOSE down --remove-orphans
    echo "✅ Stack stopped"
    ;;

  restart)
    $0 down
    $0 up
    ;;

  logs)
    SVC="${2:-}"
    if [[ -n "$SVC" ]]; then
        $COMPOSE logs -f "$SVC"
    else
        $COMPOSE logs -f
    fi
    ;;

  status)
    echo "=== Container status ==="
    $COMPOSE ps
    echo ""
    echo "=== Health checks ==="
    declare -A SERVICES=(
        ["api-gateway"]="5000"
        ["order-service"]="5001"
        ["payment-service"]="5002"
        ["inventory-service"]="5003"
        ["notification-service"]="5004"
        ["logging-service"]="5005"
        ["dashboard"]="5006"
    )
    for SVC in "${!SERVICES[@]}"; do
        PORT="${SERVICES[$SVC]}"
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                      http://localhost:${PORT}/health 2>/dev/null || echo "000")
        if [[ "$STATUS" == "200" ]]; then
            echo "  ✅ ${SVC} → HEALTHY (port ${PORT})"
        else
            echo "  ❌ ${SVC} → UNHEALTHY (HTTP ${STATUS})"
        fi
    done
    ;;

  build)
    echo "🔨 Building Docker images..."
    $COMPOSE build --parallel
    echo "✅ Build complete"
    ;;

  test)
    echo "🧪 Running test suite..."
    pip install pytest PyJWT flask flask-cors python-dotenv requests -q
    pytest tests/ -v --tb=short
    ;;

  *)
    usage
    ;;
esac
