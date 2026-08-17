# fastapi-eks-manifests

GitOps manifests repo for the DevOps Engineer assignment. Watched by ArgoCD — plain Kubernetes YAML manifests, no Helm.

## Contents (to be added)
- `rollout.yaml` — Argo Rollouts canary deployment (kind: Rollout)
- `service.yaml`
- `configmap.yaml` — non-sensitive app config (DB host, port, name)
- `secret.yaml` — DB credentials (plain K8s Secret, base64-encoded)
- `ingress.yaml` — ALB ingress with weighted traffic support for canary

Jenkins updates the image tag here directly (via `sed`/`yq`) after a successful build + scan + ECR push. ArgoCD auto-syncs this repo to the EKS cluster.
