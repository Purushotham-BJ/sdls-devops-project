#!/usr/bin/env bash
# ============================================================
# scripts/test_api.sh  —  Manual API smoke tests using curl
# Requires: curl, jq
# Usage: ./scripts/test_api.sh
# ============================================================
set -euo pipefail

BASE="http://localhost:5000"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass() { echo -e "${GREEN}✅ PASS${NC} $1"; }
fail() { echo -e "${RED}❌ FAIL${NC} $1"; }
info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

echo "================================================"
echo "  Smart Distributed Logging — API Smoke Tests"
echo "  Target: ${BASE}"
echo "================================================"
echo ""

# ── Test 1: Health check ──────────────────────────────────────────────────────
info "Test 1: Health check (public)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE}/health)
[[ "$STATUS" == "200" ]] && pass "GET /health → 200" || fail "GET /health → ${STATUS}"
echo ""

# ── Test 2: Login with valid credentials ─────────────────────────────────────
info "Test 2: Login with valid credentials"
LOGIN_RESP=$(curl -s -X POST ${BASE}/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
TOKEN=$(echo "$LOGIN_RESP" | jq -r '.token // empty')
if [[ -n "$TOKEN" ]]; then
    pass "POST /login → token received"
else
    fail "POST /login → no token (response: ${LOGIN_RESP})"
    exit 1
fi
echo ""

# ── Test 3: Login with wrong password ────────────────────────────────────────
info "Test 3: Login with wrong password"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST ${BASE}/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrongpassword"}')
[[ "$STATUS" == "401" ]] && pass "POST /login (bad creds) → 401" || fail "Expected 401, got ${STATUS}"
echo ""

# ── Test 4: Protected route without token ────────────────────────────────────
info "Test 4: POST /api/order without token (should be 401)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST ${BASE}/api/order \
  -H "Content-Type: application/json" \
  -d '{"product_id":"PROD-001","quantity":1}')
[[ "$STATUS" == "401" ]] && pass "POST /api/order (no token) → 401" || fail "Expected 401, got ${STATUS}"
echo ""

# ── Test 5: Protected route with valid token ──────────────────────────────────
info "Test 5: POST /api/order with valid JWT"
RESP=$(curl -s -X POST ${BASE}/api/order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"product_id":"PROD-001","quantity":1,"customer_id":"CUST-0001"}')
SUCCESS=$(echo "$RESP" | jq -r '.success // "unknown"')
[[ "$SUCCESS" != "unknown" ]] && pass "POST /api/order (with token) → accepted by gateway" \
                               || fail "POST /api/order (with token) → unexpected response: ${RESP}"
echo ""

# ── Test 6: GET /api/inventory ────────────────────────────────────────────────
info "Test 6: GET /api/inventory with JWT"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET ${BASE}/api/inventory \
  -H "Authorization: Bearer ${TOKEN}")
[[ "$STATUS" != "401" ]] && pass "GET /api/inventory (with token) → not 401 (got ${STATUS})" \
                           || fail "GET /api/inventory (with token) → got 401"
echo ""

# ── Test 7: Bulk simulate ─────────────────────────────────────────────────────
info "Test 7: POST /api/simulate/bulk (3 orders)"
RESP=$(curl -s -X POST ${BASE}/api/simulate/bulk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"count":3}')
SIMULATED=$(echo "$RESP" | jq -r '.simulated // 0')
[[ "$SIMULATED" == "3" ]] && pass "POST /api/simulate/bulk → simulated=3" \
                           || fail "Expected simulated=3, got: ${RESP}"
echo ""

echo "================================================"
echo "  Smoke tests complete"
echo "================================================"
