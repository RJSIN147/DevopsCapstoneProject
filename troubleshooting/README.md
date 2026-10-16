# Troubleshooting lab

Three manifests that are broken on purpose. Apply one, find out what's wrong using only kubectl, fix it, then delete it.

## 1. Image that doesn't exist (`broken-image.yaml`)

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n clinicdesk -l app=broken-image
kubectl describe pod -n clinicdesk -l app=broken-image
kubectl get events -n clinicdesk --sort-by=.lastTimestamp | tail
```

What you see: status `ErrImagePull`, then `ImagePullBackOff`. The events at the bottom of `describe` say the manifest for `this-tag-does-not-exist` was not found.

Fix: point the image at a tag that really exists in GHCR (CI tags every image with the commit SHA):

```bash
kubectl set image -n clinicdesk deploy/clinicdesk-broken-image backend=ghcr.io/rjsin147/clinicdesk-backend:<sha>
```

If the tag exists but you still get `ImagePullBackOff`, check whether the GHCR package is private. Either make it public or add an `imagePullSecret`.

## 2. Service with no endpoints (`broken-service.yaml`)

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get svc -n clinicdesk
kubectl get endpointslices -n clinicdesk -l kubernetes.io/service-name=clinicdesk-broken-service
kubectl get pods -n clinicdesk --show-labels
```

What you see: the service exists and has a ClusterIP, but the endpoint slice is empty. Comparing the selector with the pod labels shows `component: backed` instead of `backend`.

Fix the selector and the endpoints show up straight away:

```bash
kubectl patch svc -n clinicdesk clinicdesk-broken-service \
  -p '{"spec":{"selector":{"app.kubernetes.io/component":"backend"}}}'
```

A service only selects pods by label. No matching labels means no endpoints, and no endpoints means no traffic.

## 3. CrashLoopBackOff from a wrong DB host (`crashloop-bad-db.yaml`)

Put a real image tag in the file first.

```bash
kubectl apply -f troubleshooting/crashloop-bad-db.yaml
kubectl get pods -n clinicdesk -l app=bad-db -w
kubectl logs -n clinicdesk -l app=bad-db --previous
```

What you see: the pod starts, exits, and the restart count keeps going up. `logs --previous` shows Alembic failing with `could not translate host name "postgres-typo"`.

Fix: set `DATABASE_URL` to the real service (`clinicdesk-postgres`), or better, read it from the `clinicdesk-db` secret like the real deployment does.

## Cleanup

```bash
kubectl delete -f troubleshooting/ --ignore-not-found
```

## Commands I ended up using the most

| Problem | First thing to run |
|---|---|
| Pod stuck in Pending | `kubectl describe pod` (look at Events, usually PVC or not enough CPU) |
| ImagePullBackOff | `kubectl describe pod`, check the image name and tag |
| CrashLoopBackOff | `kubectl logs <pod> --previous` |
| Running but not Ready | `kubectl describe pod`, the readiness probe failure is in Events |
| Service not reachable | `kubectl get endpointslices`, then compare labels |
| Ingress returns 404 | `kubectl describe ingress`, check host and the ingress controller pods |
| HPA shows `<unknown>` | metrics-server is missing or pods have no CPU requests |
