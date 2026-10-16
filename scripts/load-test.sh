#!/usr/bin/env bash
# Generates enough traffic to make the HPA scale and the Grafana panels move.
#
#   ./scripts/load-test.sh                         # http://clinicdesk.local, 120s, 20 workers
#   ./scripts/load-test.sh http://localhost:3000 60 10
#   HOST_HEADER=clinicdesk.local ./scripts/load-test.sh http://127.0.0.1:8081   # through a port-forwarded ingress
#
# Watch it scale in another terminal with:  kubectl get hpa -n clinicdesk -w

set -euo pipefail

BASE_URL="${1:-http://clinicdesk.local}"
DURATION="${2:-120}"
WORKERS="${3:-20}"

CURL_OPTS=(-s -o /dev/null)
HEY_OPTS=()
if [ -n "${HOST_HEADER:-}" ]; then
  CURL_OPTS+=(-H "Host: $HOST_HEADER")
  HEY_OPTS+=(-host "$HOST_HEADER")
fi

if ! curl -fsS ${HOST_HEADER:+-H "Host: $HOST_HEADER"} "$BASE_URL/api/doctors" > /dev/null; then
  echo "can't reach $BASE_URL/api/doctors, is the app up and the host in /etc/hosts?" >&2
  exit 1
fi

if command -v hey > /dev/null; then
  echo "using hey: ${WORKERS} workers for ${DURATION}s against $BASE_URL"
  hey -z "${DURATION}s" -c "$WORKERS" "${HEY_OPTS[@]}" "$BASE_URL/api/appointments/stats"
  exit 0
fi

echo "hey not installed, falling back to curl loops (${WORKERS} workers, ${DURATION}s)"
end=$((SECONDS + DURATION))

worker() {
  local n=0
  while [ $SECONDS -lt $end ]; do
    curl "${CURL_OPTS[@]}" "$BASE_URL/api/appointments/stats"
    curl "${CURL_OPTS[@]}" "$BASE_URL/api/appointments"
    curl "${CURL_OPTS[@]}" "$BASE_URL/api/doctors"
    # a 404 now and then so the 4xx line on the status panel has something to show
    if (( n % 25 == 0 )); then curl "${CURL_OPTS[@]}" "$BASE_URL/api/appointments/999999"; fi
    n=$((n + 1))
  done
}

for _ in $(seq "$WORKERS"); do
  worker &
done
wait
echo "done"
