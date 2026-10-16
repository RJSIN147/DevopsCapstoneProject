# Screenshots

Evidence for each grading module. Drop the PNGs in this folder with these names so the links in the main README work.

| File | What it should show | Module |
|---|---|---|
| `app-compose.png` | the app at http://localhost:3000 with a few appointments | M1 |
| `pytest-pass.png` | `pytest -v` with all tests passing | M2 |
| `git-log.png` | commit history (10+ commits) | M3 |
| `compose-up.png` | `docker compose up --build` running | M4 |
| `github-actions-green.png` | a green run of ClinicDesk CI/CD | M5 |
| `ghcr-packages.png` | GHCR package page with SHA tags | M5 |
| `trivy-scan.png` | the Trivy step output from the pipeline | M6 |
| `terraform-plan.png` | `terraform plan` output | M7 |
| `aws-vpc.png` | VPC in the AWS console (ap-south-1) | M7 |
| `aws-eks.png` | EKS cluster + node group in the AWS console | M7 |
| `terraform-destroy.png` | `terraform destroy` finished | M7 |
| `kubectl-get-pods.png` | `kubectl get pods -n clinicdesk`, all Running | M8 |
| `kubectl-get-svc.png` | `kubectl get svc -n clinicdesk` | M8 |
| `helm-list.png` | `helm list -n clinicdesk` | M8 |
| `app-via-ingress.png` | browser on the ingress host / load balancer | M8 |
| `argocd-synced.png` | ArgoCD app Synced + Healthy | M10 video |
| `hpa-scaling.png` | `kubectl get hpa -w` while the load test runs | M8 |
| `metrics-endpoint.png` | `curl .../metrics` output | M9 |
| `prometheus-targets-up.png` | Prometheus Targets page, clinicdesk backend UP | M9 |
| `grafana-dashboard.png` | ClinicDesk dashboard with live data | M9 |

TODO: none of these are taken yet.
