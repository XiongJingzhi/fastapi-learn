#!/usr/bin/env bash

set -euo pipefail

COLLECTION="${COLLECTION:-study/testing/postman/fastapi-learning.postman_collection.json}"
ENV_FILE="${ENV_FILE:-study/testing/postman/fastapi-learning.local.postman_environment.json}"
FOLDER="${FOLDER:-Level1 - 01 Request Validation}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
REPORT_DIR="${REPORT_DIR:-study/testing/newman}"

mkdir -p "${REPORT_DIR}"

if command -v newman >/dev/null 2>&1; then
  RUNNER=(newman)
elif command -v npx >/dev/null 2>&1; then
  RUNNER=(npx -y newman)
else
  echo "newman or npx is required"
  exit 1
fi

echo "Running Postman collection folder: ${FOLDER}"
echo "Base URL: ${BASE_URL}"

"${RUNNER[@]}" run "${COLLECTION}" \
  -e "${ENV_FILE}" \
  --folder "${FOLDER}" \
  --env-var "base_url=${BASE_URL}" \
  --reporters "cli,junit" \
  --reporter-junit-export "${REPORT_DIR}/newman-report.xml"

echo "Newman report: ${REPORT_DIR}/newman-report.xml"
