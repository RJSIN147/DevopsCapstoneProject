# ClinicDesk

ClinicDesk is an appointment desk for a small multi-doctor clinic. The receptionist books patients into a doctor's slot, checks them in when they arrive, and marks the visit complete when they leave. The app refuses to double-book a doctor and keeps live counts for the day.

I built it as my DevOps final capstone. The app is deliberately small. The point of the project is everything around it: tests, containers, a CI/CD pipeline with a security gate, AWS infrastructure in Terraform, a Helm chart on Kubernetes with ingress and autoscaling, GitOps with ArgoCD, and monitoring with Prometheus and Grafana.

> Demo video and slides are in [`demo/`](demo/). Screenshots for grading are in [`docs/screenshots/`](docs/screenshots/).

---

## Contents

1. [Architecture](#architecture)
2. [Tech stack](#tech-stack)
3. [Repository layout](#repository-layout)
4. [The application](#the-application)
5. [Run it locally (Docker Compose)](#run-it-locally-docker-compose)
6. [Run without Docker](#run-without-docker)
7. [Tests](#tests)
8. [CI/CD pipeline](#cicd-pipeline)
9. [Security scanning (Trivy)](#security-scanning-trivy)
10. [Terraform (AWS VPC + EKS)](#terraform-aws-vpc--eks)
11. [Kubernetes + Helm](#kubernetes--helm)
12. [GitOps with ArgoCD](#gitops-with-argocd)
13. [Observability (Prometheus + Grafana)](#observability-prometheus--grafana)
14. [Autoscaling (HPA)](#autoscaling-hpa)
15. [Troubleshooting lab](#troubleshooting-lab)
16. [Known issues and limitations](#known-issues-and-limitations)
17. [Submission checklist](#submission-checklist)

---

## Architecture

```text
 Developer ── git push ──> GitHub (RJSIN147/DevopsCapstoneProject)
                               │
                               ▼
                       GitHub Actions
       ┌───────────────┬───────┴────────┬────────────────┐
   pytest + ruff   npm test/build   helm lint +    secret scan
       └───────────────┴──────┬─────── terraform validate
                              ▼
               docker build (backend, frontend)
                              ▼
                 Trivy scan, fail on HIGH/CRITICAL
                              ▼
            push to GHCR, tag = git commit SHA
                              ▼
         kind cluster: helm install + helm test (smoke test)
                              ▼
          (optional) bump tag in values-prod.yaml ──> ArgoCD
                                                        │
 Terraform ──> AWS ap-south-1                           │ sync
               VPC (2 public + 2 private subnets, NAT)  │
               EKS 1.34, managed node group  <──────────┘
                     │
                     ▼
     ingress-nginx  ──  /      ──> frontend Service ──> nginx pods (React build)
                    └─  /api   ──> backend Service  ──> FastAPI pods (HPA 2..8)
                                                          │
                                                          ▼
                                               PostgreSQL StatefulSet + EBS volume
     kube-prometheus-stack
       Prometheus ── ServiceMonitor ──> backend /metrics
       Grafana    ── dashboard ConfigMap shipped with the chart
```

Request path in the browser: the React app only ever calls `/api/...` on its own origin. Locally nginx in the frontend container proxies that to the backend. On Kubernetes the Ingress sends `/api` straight to the backend service, so the browser never needs to know an internal hostname.

## Tech stack

| Layer | What I used |
|---|---|
| Frontend | React 19, Vite 8, plain CSS (responsive, no UI framework) |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2 |
| Database | PostgreSQL 17, Alembic migrations |
| Tests | pytest + FastAPI TestClient (in-memory SQLite), node:test for frontend helpers, ruff for lint |
| Containers | Docker multi-stage builds, nginx-unprivileged, Docker Compose |
| CI/CD | GitHub Actions |
| Security | Trivy (image CVEs + repo secret scan), GitHub code scanning (SARIF) |
| Registry | GitHub Container Registry (ghcr.io) |
| Infrastructure | Terraform, AWS VPC, EKS, EBS CSI driver |
| Kubernetes | Helm 3 chart, ingress-nginx, HPA, PodDisruptionBudget, ResourceQuota |
| GitOps | ArgoCD |
| Monitoring | kube-prometheus-stack (Prometheus Operator, Grafana), prometheus-fastapi-instrumentator |

## Repository layout

```text
.
├── backend/                 FastAPI app
│   ├── app/                 main.py, models, schemas, routers/, metrics.py
│   ├── alembic/versions/    0001 tables, 0002 seed doctors
│   ├── tests/               pytest suite (25 tests)
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/                React + Vite app, nginx config template, Dockerfile
├── docker-compose.yml       postgres + backend + frontend
├── .github/workflows/       ci-cd.yml
├── terraform/               VPC + EKS
├── helm/clinicdesk/         Helm chart (values.yaml, values-dev.yaml, values-prod.yaml)
├── k8s/                     namespace, gp3 storage class, resource quota
├── argocd/                  ArgoCD Application manifests
├── monitoring/              kube-prometheus-stack values
├── troubleshooting/         broken manifests for the troubleshooting lab
├── scripts/load-test.sh     traffic generator for the HPA / Grafana demo
├── demo/                    presentation video + slides
└── docs/screenshots/        evidence for grading
```

## The application

### What you can do in the UI

- See today's numbers: appointments today, patients in the waiting room, completed, cancelled
- Filter the schedule by day, doctor and status
- Book an appointment (patient, phone, doctor, date, time, length, reason)
- Move an appointment along: Booked -> Checked in -> Completed, or Cancel
- Add doctors, pause a doctor so nobody can book them, remove a doctor who has no history

The layout works on a phone too. The sidebar turns into a top bar and the table rows turn into cards.

### API

Swagger UI is at `/docs` when the backend is running.

| Method | Path | What it does |
|---|---|---|
| GET | `/` | service name and version |
| GET | `/health` | liveness, always `UP` if the process answers |
| GET | `/ready` | readiness, runs `SELECT 1` against Postgres, 503 if it fails |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/doctors` | list doctors (`?active=true` to filter) |
| GET | `/api/doctors/{id}` | one doctor |
| POST | `/api/doctors` | add a doctor |
| PUT | `/api/doctors/{id}` | update / pause a doctor |
| DELETE | `/api/doctors/{id}` | delete, 409 if they have appointments |
| GET | `/api/appointments` | list, filters `?status=`, `?doctor_id=`, `?on=YYYY-MM-DD` |
| GET | `/api/appointments/stats` | counts for the dashboard cards |
| GET | `/api/appointments/{id}` | one appointment |
| POST | `/api/appointments` | book, 409 if the doctor's slot overlaps another booking |
| PUT | `/api/appointments/{id}` | reschedule or change status |
| DELETE | `/api/appointments/{id}` | delete |

The rules the backend enforces:

- no overlapping bookings for the same doctor (cancelled ones don't count)
- a paused doctor can't take new bookings
- times are stored in UTC; "today" and the day filter use the clinic's timezone (`CLINIC_TIMEZONE`, default `Asia/Kolkata`)
- a doctor with history can't be deleted, only paused, so old appointments keep their doctor

### Database

Two tables, `doctors` and `appointments`, created by Alembic migration `0001_initial`. Migration `0002_seed_doctors` adds four doctors so the app isn't empty on first start.

The backend container runs `alembic upgrade head` before starting uvicorn. On Kubernetes there are at least two backend pods starting at the same time, so `alembic/env.py` takes a Postgres advisory lock first. One pod runs the migrations and the others wait, then find nothing to do.

To look at the data:

```bash
# compose
docker compose exec postgres psql -U clinicdesk -d clinicdesk -c "select * from appointments;"
# kubernetes
kubectl exec -n clinicdesk clinicdesk-postgres-0 -- psql -U clinicdesk -d clinicdesk -c "select * from appointments;"
```

## Run it locally (Docker Compose)

Needs Docker with the compose plugin.

```bash
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:3000 | the app |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/health | liveness |
| http://localhost:8000/ready | readiness |
| http://localhost:8000/metrics | Prometheus metrics |

Postgres is published on `127.0.0.1:5433` (not 5432, so it doesn't clash with a Postgres already installed on the laptop). Change it with `POSTGRES_HOST_PORT=...`.

Compose waits for the Postgres health check before starting the backend, and for the backend health check before starting the frontend.

```bash
docker compose down        # stop
docker compose down -v     # stop and delete the database volume
```

Both images run as non-root users: the backend as uid 10001, the frontend as nginx uid 101 (it listens on 8080 for that reason).

## Run without Docker

Backend (needs a Postgres somewhere, e.g. `docker compose up postgres`):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://clinicdesk:clinicdesk@localhost:5433/clinicdesk'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, /api is proxied to localhost:8000
```

## Tests

```bash
cd backend
pytest -v
ruff check . && ruff format --check .
```

There are 25 tests across `test_health.py`, `test_doctors.py` and `test_appointments.py`. They cover health/ready/metrics, doctor CRUD, booking, validation errors, double-booking, back-to-back slots, rebooking a cancelled slot, status changes, rescheduling into a taken slot, filters (including a day boundary that differs between UTC and the clinic timezone) and stats.

The tests never touch Postgres. `tests/conftest.py` forces `DATABASE_URL=sqlite://`, builds a fresh in-memory SQLite database for every single test and swaps it in with FastAPI's `dependency_overrides`. Every test starts from an empty database and the order doesn't matter.

Frontend helpers (date conversion, status transitions, error parsing) have a few `node:test` tests:

```bash
cd frontend && npm test
```

Evidence: `docs/screenshots/pytest-pass.png` (TODO: add screenshot of `pytest -v`)

## CI/CD pipeline

Workflow: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml). It runs on every push and pull request to `main`, and can be started by hand (workflow_dispatch).

| Stage | Job | What happens |
|---|---|---|
| 1. Test | `backend-test` | ruff lint + format check, `pytest -v`, JUnit report uploaded |
| | `frontend-build` | `npm ci`, `npm test`, `npm run build` |
| | `iac-validate` | `helm lint` with every values file, `terraform fmt -check` + `validate` |
| | `secret-scan` | Trivy filesystem scan for committed keys/tokens |
| 2. Build | `build-scan-push` (matrix: backend, frontend) | docker build, Trivy report, Trivy gate, push to GHCR |
| 3. Deploy test | `deploy-smoke-test` | creates a kind cluster, loads the new images, `helm upgrade --install`, `helm test`, books an appointment through the frontend service |
| 4. GitOps | `gitops-bump` | writes the new SHA into `values-prod.yaml` so ArgoCD deploys it (off unless the repo variable `GITOPS_AUTO_BUMP=true` is set) |

If any test fails, the build job never starts, so a broken commit never produces an image. The push and deploy steps only run for pushes to `main`. Pull requests get tested and scanned but don't publish anything.

Image tags are the full commit SHA, never `latest`:

```text
ghcr.io/rjsin147/clinicdesk-backend:<commit-sha>
ghcr.io/rjsin147/clinicdesk-frontend:<commit-sha>
```

So any running pod can be traced back to the exact commit it was built from (`kubectl get deploy -n clinicdesk -o wide` shows the tag).

Evidence:
- Pipeline run: https://github.com/RJSIN147/DevopsCapstoneProject/actions/runs/38954914310 (all jobs green, including the kind smoke deploy)
- `docs/screenshots/github-actions-green.png` (TODO)
- `docs/screenshots/ghcr-packages.png` (TODO, the package page showing SHA tags)

## Security scanning (Trivy)

Each image goes through Trivy twice in the `build-scan-push` job:

1. A full report with every severity, saved as a build artifact (`trivy-backend`, `trivy-frontend`) and uploaded to the GitHub Security tab as SARIF.
2. The gate: `trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1`. If any HIGH or CRITICAL CVE with a fix available is found, the job fails and the image is not pushed.

`--ignore-unfixed` is there because a CVE without a fixed package version can't be solved by rebuilding, and blocking on it would just block every build. Exceptions we accept on purpose go in `.trivyignore` with a reason.

Things I did in the Dockerfiles to keep the scan clean:
- `python:3.12-slim` and `nginxinc/nginx-unprivileged:1.30-alpine` as small, current bases
- multi-stage builds, so node, npm and build tools never reach the runtime images
- removed `pip` from the backend runtime image (it's only needed at build time)
- current versions of every Python dependency (old Starlette/h11 versions have known CVEs)

What the scan result means (from run [38953967054](https://github.com/RJSIN147/DevopsCapstoneProject/actions/runs/38953967054)):

Trivy scanned the Debian 13 OS packages and all the Python libraries in the backend image, and the Alpine 3.24 packages in the frontend image. The gate found 0 fixable HIGH or CRITICAL vulnerabilities in either image, so both were pushed. The full backend report still lists 166 findings (44 HIGH) in Debian base packages, but none of them have a fixed version released yet. They aren't something a rebuild can solve today, and they'll disappear on their own once Debian ships the fix and CI rebuilds the image. The Python libraries came back clean, and the frontend had a single MEDIUM in an Alpine package.

The first pipeline run actually failed this gate. Trivy found 4 HIGH CVEs (two in urllib3, CVE-2026-97687 and CVE-2026-97689, plus one in msgpack and CVE-2025-47273 in setuptools). None of these were my dependencies. They were copies that pip vendors inside itself, sitting in the image's virtualenv. pip isn't needed once the dependencies are installed, so the Dockerfile now uninstalls it in the build stage and the next run passed.

Evidence: `docs/screenshots/trivy-scan.png` (TODO)

Other security bits:
- containers run as non-root, drop all Linux capabilities, `allowPrivilegeEscalation: false`, seccomp `RuntimeDefault`, and the backend has a read-only root filesystem
- the namespace has Pod Security `restricted` set to warn/audit
- no credentials in git: AWS creds come from the AWS CLI profile, the prod DB password and the Grafana admin password come from Kubernetes secrets created by hand, `*.tfvars` and `.env` are gitignored
- repo secret scan in CI

## Terraform (AWS VPC + EKS)

Code: [`terraform/`](terraform/). More detail in [`terraform/README.md`](terraform/README.md).

What it creates in `ap-south-1`:

- VPC `10.30.0.0/16` across 2 availability zones
- 2 public subnets (load balancers, NAT) and 2 private subnets (worker nodes), tagged for Kubernetes load balancer discovery
- 1 NAT gateway
- EKS cluster `clinicdesk-eks` on Kubernetes 1.34 with a public API endpoint
- a managed node group, 2 x t3.medium (scales 2 to 4), Amazon Linux 2023
- addons: CoreDNS, kube-proxy, VPC CNI, Pod Identity agent, EBS CSI driver (with its own IAM role through IRSA, needed for the Postgres volume)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
$(terraform output -raw configure_kubectl)
kubectl get nodes
```

When finished (uninstall the Helm releases first so the load balancer is gone):

```bash
terraform destroy
```

Evidence:
- `docs/screenshots/terraform-plan.png` (TODO)
- `docs/screenshots/aws-vpc.png` and `docs/screenshots/aws-eks.png` (TODO)
- `docs/screenshots/terraform-destroy.png` (TODO)

## Kubernetes + Helm

### What the chart deploys

Chart: [`helm/clinicdesk/`](helm/clinicdesk/)

| Object | Notes |
|---|---|
| Deployment `clinicdesk-backend` | 2+ replicas, init container waits for Postgres, startup/readiness/liveness probes on `/health` and `/ready` |
| Deployment `clinicdesk-frontend` | 2 replicas, nginx serving the React build, told where the backend is through `BACKEND_URL` |
| StatefulSet `clinicdesk-postgres` | 1 replica with a PersistentVolumeClaim |
| Services | all ClusterIP: backend :8000, frontend :80, postgres :5432 |
| Ingress | `/api` -> backend, `/` -> frontend, class `nginx` |
| HPA | backend 2 to 6 pods (2 to 8 in prod) at 60% CPU, frontend optional |
| PodDisruptionBudget | keeps at least 1 backend pod during node drains |
| Secret | DB credentials and the full `DATABASE_URL` (or use an existing secret) |
| ServiceMonitor | tells Prometheus to scrape the backend, only rendered if the CRD exists |
| ConfigMap | Grafana dashboard JSON, picked up by the Grafana sidecar |
| helm test pod | checks `/ready` and the frontend -> backend proxy |

Values files:
- `values.yaml`: defaults
- `values-dev.yaml`: minikube, locally built images, ingress on `clinicdesk.local`
- `values-prod.yaml`: EKS, GHCR images by SHA, gp3 storage, DB password from an existing secret

### Local Kubernetes (minikube)

```bash
minikube start
minikube addons enable ingress
minikube addons enable metrics-server

# build the images and copy them into minikube (no registry needed)
docker compose build
minikube image load clinicdesk-backend:local
minikube image load clinicdesk-frontend:local

kubectl apply -f k8s/namespace.yaml -f k8s/resource-quota.yaml
helm upgrade --install clinicdesk ./helm/clinicdesk -n clinicdesk -f helm/clinicdesk/values-dev.yaml --wait
helm test clinicdesk -n clinicdesk

kubectl get pods -n clinicdesk
kubectl get svc -n clinicdesk
kubectl get ingress -n clinicdesk
helm list -n clinicdesk
```

To open it through the ingress, add `clinicdesk.local` to `/etc/hosts`. With the Docker driver on Docker Desktop the minikube IP isn't reachable from the host, so forward the ingress controller instead:

```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8081:80
echo "127.0.0.1 clinicdesk.local" | sudo tee -a /etc/hosts
# open http://clinicdesk.local:8081
```

(`minikube tunnel` plus the minikube IP in `/etc/hosts` also works.)

### Deploying to EKS

After `terraform apply`:

```bash
# 1. storage class (EKS has no default one) and namespace
kubectl apply -f k8s/storageclass-gp3.yaml -f k8s/namespace.yaml -f k8s/resource-quota.yaml

# 2. ingress controller, this creates an AWS load balancer
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace

# 3. database secret for prod (pick a real password)
PW='<choose-a-db-password>'
kubectl create secret generic clinicdesk-db-prod -n clinicdesk \
  --from-literal=username=clinicdesk \
  --from-literal=password="$PW" \
  --from-literal=database=clinicdesk \
  --from-literal=database-url="postgresql+psycopg://clinicdesk:${PW}@clinicdesk-postgres:5432/clinicdesk"

# 4. monitoring first, so the ServiceMonitor gets created with the app (see monitoring/README.md)

# 5. the app, either with ArgoCD (next section) or straight with helm:
SHA=<commit sha of a green pipeline run>
helm upgrade --install clinicdesk ./helm/clinicdesk -n clinicdesk \
  -f helm/clinicdesk/values-prod.yaml \
  --set backend.image.tag=$SHA --set frontend.image.tag=$SHA --wait

# 6. find the load balancer hostname and open it
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

For a quick demo without a domain, point the ingress host at the load balancer: `--set ingress.host=<elb-hostname>`, or add the load balancer IP to `/etc/hosts` as `clinicdesk.example.com`.

The GHCR packages need to be public for EKS to pull them without credentials (GitHub -> your profile -> Packages -> clinicdesk-backend -> Package settings -> Change visibility). The alternative is a docker-registry secret plus `imagePullSecrets` in the values.

Evidence:
- `docs/screenshots/kubectl-get-pods.png` (TODO)
- `docs/screenshots/kubectl-get-svc.png` (TODO)
- `docs/screenshots/helm-list.png` (TODO)
- `docs/screenshots/app-via-ingress.png` (TODO)

## GitOps with ArgoCD

[`argocd/application.yaml`](argocd/application.yaml) points ArgoCD at `helm/clinicdesk` on the `main` branch of this repo with `values-prod.yaml`. Automated sync, prune and self-heal are on. If someone changes something in the cluster by hand, ArgoCD puts it back to what git says.

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -n argocd -f argocd/application.yaml

# UI
kubectl port-forward -n argocd svc/argocd-server 8443:443
kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

For minikube there's `argocd/application-dev.yaml`, which uses `values-dev.yaml` and the locally loaded images.

The GitOps flow end to end:

```text
git push -> CI tests, builds, scans, pushes ghcr.io/...:<sha>
         -> gitops-bump commits values-prod.yaml with tag <sha>
         -> ArgoCD notices the new commit, syncs, pods roll to the new image
```

The tag bump is a commit made by the pipeline, so it's switched off until you add the repository variable `GITOPS_AUTO_BUMP` = `true` (Settings -> Secrets and variables -> Actions -> Variables). Without it, update the two `tag:` lines in `values-prod.yaml` to the SHA of a green run and push; ArgoCD picks it up the same way.

Evidence: `docs/screenshots/argocd-synced.png` (TODO)

## Observability (Prometheus + Grafana)

Details and install commands: [`monitoring/README.md`](monitoring/README.md).

- The backend exposes `/metrics` through `prometheus-fastapi-instrumentator`: request count, latency histogram, status codes per endpoint.
- I added three app-level counters in `backend/app/metrics.py`: bookings, rejected double bookings, and status changes.
- `kube-prometheus-stack` installs Prometheus, the operator and Grafana. The chart's `ServiceMonitor` makes Prometheus scrape the backend every 15 seconds.
- The Grafana dashboard ("ClinicDesk - API overview") ships with the chart as a ConfigMap, so it shows up in Grafana with no clicking. Panels: requests/sec, 5xx ratio, p95 latency, bookings in the last hour, blocked double bookings, backend pods up, request rate per endpoint, p50/p95 latency per endpoint, responses by status class, status changes, CPU and memory per backend pod.

```bash
curl http://localhost:8000/metrics | head -30     # compose
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

Evidence:
- `docs/screenshots/metrics-endpoint.png` (TODO)
- `docs/screenshots/prometheus-targets-up.png` (TODO)
- `docs/screenshots/grafana-dashboard.png` (TODO)

## Autoscaling (HPA)

The backend HPA scales between 2 and 6 pods (8 in prod) and targets 60% average CPU. It works because every container has CPU requests set and metrics-server is running (minikube addon; on EKS install it with `helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system` from the `https://kubernetes-sigs.github.io/metrics-server/` repo).

Normal clicking around won't push CPU anywhere near 60%, so there's a load script:

```bash
# terminal 1
kubectl get hpa -n clinicdesk -w
# terminal 2
./scripts/load-test.sh http://clinicdesk.local:8081 180 30
```

It uses `hey` if installed, plain curl loops otherwise. Scale-down has a 2 minute stabilization window so the pods don't disappear the second the load stops.

Evidence: `docs/screenshots/hpa-scaling.png` (TODO)

## Troubleshooting lab

[`troubleshooting/`](troubleshooting/) has three broken manifests and a write-up of how to find each problem:

1. `broken-image.yaml`: tag that doesn't exist -> `ImagePullBackOff`
2. `broken-service.yaml`: selector typo -> service with no endpoints
3. `crashloop-bad-db.yaml`: wrong DB host -> `CrashLoopBackOff`, found with `kubectl logs --previous`

## Known issues and limitations

- **No login.** Anyone who can reach the URL can book and delete. A real clinic app needs staff accounts (OAuth/OIDC in front, or JWT in FastAPI) and an audit log. Out of scope for this project.
- **Postgres runs inside the cluster** as a single StatefulSet pod with no backups and no replica. Fine for the demo. In production I'd move to Amazon RDS (Multi-AZ, automated backups) and set `postgres.enabled=false` + `postgres.externalHost`.
- **No TLS on the ingress yet.** The commented block in `values-prod.yaml` shows the cert-manager setup once there's a real domain.
- **One NAT gateway** to save money, so it's a single point of failure for outbound traffic from the private subnets.
- **ingress-nginx** is what the course used, but the upstream project has been retired. Moving to Gateway API (or the AWS Load Balancer Controller on EKS) would be the next step.
- **Patient data:** the app stores names and phone numbers. That's personal health data, so a real deployment would also need encryption at rest for the DB (the gp3 storage class already sets `encrypted: "true"`), access logging and a retention policy.
- **Timezones:** times are stored in UTC and the browser shows them in its local time, while "today" is worked out in `CLINIC_TIMEZONE`. If a browser in another timezone opens the app the two can disagree near midnight. One clinic, one timezone, so I left it like that.
- **Terraform state is local** by default. The S3 backend block is there, commented out, for shared state.
- **GHCR visibility:** packages may need to be made public by hand before EKS can pull them.

## Submission checklist

```text
Application
  [x] GitHub repo: https://github.com/RJSIN147/DevopsCapstoneProject
  [x] docker compose up --build runs postgres, backend, frontend
  [x] 4+ REST endpoints (GET/POST/PUT/DELETE on doctors and appointments)
  [x] Alembic migrations in backend/alembic/versions
  [ ] screenshot of the app in the browser             docs/screenshots/app-compose.png

Testing
  [x] 25 pytest tests, in-memory SQLite, pytest.ini + conftest.py
  [ ] pytest -v screenshot                             docs/screenshots/pytest-pass.png

Docker
  [x] backend/Dockerfile, frontend/Dockerfile (multi-stage)
  [x] non-root in both images
  [ ] docker compose up screenshot                     docs/screenshots/compose-up.png

CI/CD
  [x] workflow runs on push to main, pytest gates the build
  [x] images pushed to GHCR tagged with the commit SHA
  [ ] link to a green run + GHCR screenshot

Security
  [x] Trivy scan on both images, fails on HIGH/CRITICAL
  [x] no secrets in git (secret scan in CI)
  [ ] Trivy output screenshot + written explanation above

Terraform
  [x] terraform.tfvars.example, no credentials
  [ ] plan / AWS console / destroy screenshots

Kubernetes + Helm
  [ ] kubectl get pods, svc, helm list, app through ingress screenshots

Observability
  [ ] /metrics, Prometheus targets UP, Grafana dashboard screenshots

Documentation
  [x] README.md
  [ ] demo/presentation.mp4                            MANDATORY
  [x] demo/ClinicDesk-Capstone.pptx (slides)
```
