# Screenshots

Evidence for each grading module. The Kubernetes, ArgoCD and monitoring ones were taken on my local minikube cluster. The AWS/EKS ones still have to be taken once the Terraform cluster is up.

| File | What it shows | Module | Status |
|---|---|---|---|
| [`app-compose.png`](app-compose.png) | the app at http://localhost:3000 with today's appointments | M1 | done |
| [`app-booking-conflict.png`](app-booking-conflict.png) | booking modal rejecting a double booking (409 from the API) | M1 | done |
| [`api-docs.png`](api-docs.png) | Swagger UI at http://localhost:8000/docs | M1 | done |
| [`pytest-pass.png`](pytest-pass.png) | `pytest -v`, 25 passed | M2 | done |
| [`git-log.png`](git-log.png) | commit history (`git log`) | M3 | done |
| [`compose-up.png`](compose-up.png) | `docker compose up --build` with all three services up | M4 | done |
| [`github-actions-green.png`](github-actions-green.png) | a green run of ClinicDesk CI/CD | M5 | done |
| `ghcr-packages.png` | GHCR package page with SHA tags | M5 | TODO (packages are private, needs a logged-in browser) |
| [`trivy-scan.png`](trivy-scan.png) | Trivy gate output from the pipeline, both images clean | M6 | done |
| `terraform-plan.png` | `terraform plan` output | M7 | TODO (needs AWS credentials) |
| `aws-vpc.png` | VPC in the AWS console (ap-south-1) | M7 | TODO |
| `aws-eks.png` | EKS cluster + node group in the AWS console | M7 | TODO |
| `terraform-destroy.png` | `terraform destroy` finished | M7 | TODO |
| [`kubectl-get-pods.png`](kubectl-get-pods.png) | `kubectl get pods -n clinicdesk`, all Running | M8 | done (minikube) |
| [`kubectl-get-svc.png`](kubectl-get-svc.png) | services and the ingress | M8 | done (minikube) |
| [`kubectl-get-all.png`](kubectl-get-all.png) | deployments, statefulset, HPA, PDB, ServiceMonitor, PVC | M8 | done (minikube) |
| [`helm-list.png`](helm-list.png) | `helm list` + `helm status` | M8 | done (minikube) |
| [`app-via-ingress.png`](app-via-ingress.png) | the app through the ingress host clinicdesk.local | M8 | done (minikube) |
| [`hpa-scaling.png`](hpa-scaling.png) | HPA going from 2 to 6 pods under `scripts/load-test.sh` | M8 | done (minikube) |
| [`argocd-synced.png`](argocd-synced.png) | ArgoCD app Synced + Healthy | M10 video | done (minikube) |
| [`metrics-endpoint.png`](metrics-endpoint.png) | `curl .../metrics` | M9 | done |
| [`prometheus-targets-up.png`](prometheus-targets-up.png) | Prometheus target health, clinicdesk backend 2/2 UP | M9 | done (minikube) |
| [`grafana-dashboard.png`](grafana-dashboard.png) | ClinicDesk dashboard with traffic from the load test | M9 | done (minikube) |
