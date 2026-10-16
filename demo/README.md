# Demo

| File | Status |
|---|---|
| `ClinicDesk-Capstone.pptx` | slides, done |
| `presentation.mp4` | TODO: record and add (mandatory) |

## Video plan (same order as SUBMISSION.md)

1. Slides: what ClinicDesk is, architecture, tech stack (about 3 min)
2. Codebase: folder structure, `backend/app/routers/appointments.py` (double-booking check), `alembic/env.py` (migration lock), Dockerfiles, Helm chart
3. CI/CD: make a small change, push, show the Actions run going through test -> build -> Trivy -> GHCR -> kind smoke test
4. Terraform: `terraform plan`, then the VPC and EKS cluster in the AWS console
5. ArgoCD: the clinicdesk app Synced/Healthy, show it picking up the new commit
6. Kubernetes: `kubectl get pods,svc,ingress,hpa -n clinicdesk`, open the app through the ingress, book an appointment
7. Prometheus: Status -> Targets, clinicdesk backend UP
8. Grafana: ClinicDesk dashboard while `scripts/load-test.sh` runs, HPA scaling up
9. Troubleshooting: apply `troubleshooting/broken-service.yaml`, find and fix it

GitHub rejects files over 100 MB in a normal push. If the recording is bigger, compress it (`ffmpeg -i in.mp4 -vcodec libx264 -crf 28 presentation.mp4`) or attach it to a GitHub release and link it here.

Video link (if it's a release asset): TODO
