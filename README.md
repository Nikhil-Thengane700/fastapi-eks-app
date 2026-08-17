# fastapi-eks-app

Single repo (monorepo) for the DevOps Engineer assignment (Kubernetes + CI/CD Infrastructure Challenge) — app code + deployment manifests together.

## Contents
- `app/` — FastAPI application source
- `tests/` — pytest unit tests
- `k8s/` — plain Kubernetes YAML manifests (watched by ArgoCD via this specific path, not the whole repo)
- `Dockerfile` — multi-stage build (DevSecOps practices: non-root user, pinned base image)
- `Jenkinsfile` — CI/CD pipeline (test → SonarQube → build → Trivy scan → push to ECR → update image tag in `k8s/`)

## Note on structure
This is a monorepo, not the "purist" GitOps pattern of separate app-code and manifests repos. Chosen for simplicity/speed given assignment scope. ArgoCD is pointed at the `k8s/` path within this repo rather than the repo root.
