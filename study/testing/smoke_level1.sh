#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

pass() { printf "[PASS] %s\n" "$1"; }
fail() { printf "[FAIL] %s\n" "$1"; exit 1; }

check_status() {
  local name="$1"
  local expected="$2"
  local method="$3"
  local path="$4"
  local data="${5:-}"

  local code
  if [[ -n "$data" ]]; then
    code="$(curl -s -o /tmp/fastapi_smoke_resp.json -w "%{http_code}" \
      -X "$method" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "${BASE_URL}${path}")"
  else
    code="$(curl -s -o /tmp/fastapi_smoke_resp.json -w "%{http_code}" \
      -X "$method" \
      "${BASE_URL}${path}")"
  fi

  if [[ "$code" == "$expected" ]]; then
    pass "$name ($method $path => $code)"
  else
    printf "Response body:\n"
    cat /tmp/fastapi_smoke_resp.json || true
    printf "\n"
    fail "$name expected $expected but got $code"
  fi
}

echo "Smoke testing against ${BASE_URL}"

# 01_request_validation.py
check_status "health" 200 "GET" "/health"
check_status "validation error format" 422 "POST" "/users/" '{"username":"john_doe","age":25,"password":"abc12345","confirm_password":"abc12345"}'
check_status "set-cookie login" 200 "POST" "/login/" '{"username":"alice","password":"secret123"}'

# 02_response_handling.py / 03_unified_response.py / 04_error_handling.py / 05_restful_api.py
# 这些示例需单独启动对应 app，再执行以下检查。
check_status "root" 200 "GET" "/"

echo "Done. For other examples, run the corresponding app module and reuse this script with BASE_URL."
