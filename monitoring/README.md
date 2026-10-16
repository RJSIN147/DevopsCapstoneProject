# Monitoring

Prometheus and Grafana come from the `kube-prometheus-stack` chart. The ClinicDesk chart adds two things on top:

- a `ServiceMonitor` that tells Prometheus to scrape `/metrics` on the backend service every 15s
- a ConfigMap with the Grafana dashboard (`helm/clinicdesk/dashboards/clinicdesk.json`), which the Grafana sidecar loads automatically

## Install

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Grafana admin login, pick your own password
kubectl create namespace monitoring
kubectl create secret generic grafana-admin -n monitoring \
  --from-literal=admin-user=admin \
  --from-literal=admin-password='<choose-a-password>'

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/kube-prometheus-stack-values.yaml
```

Install this before the app (or run `helm upgrade` on the app afterwards). The ServiceMonitor template only renders when the CRD exists in the cluster.

## Open the UIs

```bash
# Prometheus -> Status -> Targets, look for serviceMonitor/clinicdesk/clinicdesk-backend
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090

# Grafana, log in with the user/password from the grafana-admin secret
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

In Grafana the dashboard is under Dashboards -> "ClinicDesk - API overview".

## Metrics the backend exposes

| Metric | Where it comes from |
|---|---|
| `http_requests_total{handler,method,status}` | prometheus-fastapi-instrumentator |
| `http_request_duration_seconds_bucket{handler,method}` | prometheus-fastapi-instrumentator |
| `clinicdesk_appointments_booked_total` | `app/metrics.py`, bumped on every booking |
| `clinicdesk_booking_conflicts_total` | bumped when a double booking is rejected (409) |
| `clinicdesk_appointment_status_changes_total{status}` | check in / complete / cancel |

Some useful queries to try in Prometheus:

```promql
sum by (handler) (rate(http_requests_total{namespace="clinicdesk"}[1m]))
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{namespace="clinicdesk"}[5m])))
sum(rate(http_requests_total{namespace="clinicdesk",status="5xx"}[5m]))
```

To get the panels moving, run `scripts/load-test.sh` against the ingress host.
