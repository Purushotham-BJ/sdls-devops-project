#!/usr/bin/env bash
# ============================================================
# scripts/k8s.sh — Kubernetes management helper
# Usage: ./scripts/k8s.sh [deploy|delete|status|scale|logs|hpa]
# ============================================================
set -euo pipefail

NS="sdls"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $*${NC}"; }
err()  { echo -e "${RED}❌ $*${NC}"; }
info() { echo -e "${YELLOW}ℹ️  $*${NC}"; }

cmd="${1:-status}"

case "$cmd" in

  # ── Deploy everything ──────────────────────────────────────
  deploy)
    ENV="${2:-dev}"
    info "Deploying to environment: ${ENV}"
    kubectl apply -k k8s/overlays/${ENV}
    ok "Deployment applied"
    echo ""
    kubectl rollout status deployment --namespace=${NS} --timeout=120s || true
    ;;

  # ── Delete everything ──────────────────────────────────────
  delete)
    ENV="${2:-dev}"
    info "Deleting environment: ${ENV}"
    kubectl delete -k k8s/overlays/${ENV} --ignore-not-found
    ok "Deleted"
    ;;

  # ── Status overview ────────────────────────────────────────
  status)
    echo "=== Pods ==="
    kubectl get pods -n ${NS} -o wide 2>/dev/null || echo "No pods"
    echo ""
    echo "=== Deployments ==="
    kubectl get deployments -n ${NS} 2>/dev/null || echo "No deployments"
    echo ""
    echo "=== Services ==="
    kubectl get svc -n ${NS} 2>/dev/null || echo "No services"
    echo ""
    echo "=== HPAs ==="
    kubectl get hpa -n ${NS} 2>/dev/null || echo "No HPAs"
    ;;

  # ── Manual scale ──────────────────────────────────────────
  # Usage: ./scripts/k8s.sh scale order-service 4
  scale)
    SVC="${2:?Usage: k8s.sh scale <service> <replicas>}"
    REPLICAS="${3:?Usage: k8s.sh scale <service> <replicas>}"
    kubectl scale deployment/${SVC} --replicas=${REPLICAS} -n ${NS}
    ok "Scaled ${SVC} to ${REPLICAS} replicas"
    kubectl rollout status deployment/${SVC} -n ${NS} --timeout=60s
    ;;

  # ── HPA status ────────────────────────────────────────────
  hpa)
    info "Horizontal Pod Autoscaler status:"
    kubectl get hpa -n ${NS} -o wide
    echo ""
    info "Current pod counts per deployment:"
    kubectl get deployments -n ${NS} \
      -o custom-columns="SERVICE:.metadata.name,READY:.status.readyReplicas,DESIRED:.spec.replicas"
    ;;

  # ── Stream logs ───────────────────────────────────────────
  logs)
    SVC="${2:?Usage: k8s.sh logs <service>}"
    kubectl logs -f deployment/${SVC} -n ${NS} --tail=100
    ;;

  # ── Rolling restart (redeploy without image change) ───────
  restart)
    SVC="${2:-}"
    if [[ -n "$SVC" ]]; then
      kubectl rollout restart deployment/${SVC} -n ${NS}
      ok "Restarted ${SVC}"
    else
      for d in $(kubectl get deployments -n ${NS} -o name); do
        kubectl rollout restart ${d} -n ${NS}
      done
      ok "All deployments restarted"
    fi
    ;;

  *)
    echo "Usage: $0 [deploy|delete|status|scale|logs|hpa|restart]"
    echo "  deploy [dev|prod]            Deploy with Kustomize overlay"
    echo "  delete [dev|prod]            Delete all resources"
    echo "  status                       Show pods / deployments / HPAs"
    echo "  scale <service> <replicas>   Manually set replica count"
    echo "  hpa                          Show autoscaler status"
    echo "  logs <service>               Stream service logs"
    echo "  restart [service]            Rolling restart"
    ;;
esac
