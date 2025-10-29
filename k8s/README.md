# Kubernetes Manifests

This directory contains raw Kubernetes manifests for deploying SoundHash.

## Files

- `namespace.yaml` - Namespaces for production and staging
- `secrets.yaml.template` - Template for secrets (DO NOT commit actual secrets)
- `configmap.yaml` - Application configuration
- `deployment.yaml` - API deployment with 3 replicas
- `service.yaml` - LoadBalancer service and ServiceAccount
- `pvc.yaml` - Persistent Volume Claims for storage
- `hpa.yaml` - Horizontal Pod Autoscaler
- `ingress.yaml` - Ingress with TLS/SSL
- `cert-manager.yaml` - Let's Encrypt SSL certificates
- `pgbouncer.yaml` - PostgreSQL connection pooler
- `redis.yaml` - Redis StatefulSet

## Quick Deploy

### 1. Create Secrets

```bash
kubectl create secret generic soundhash-secrets \
  --namespace=soundhash-production \
  --from-literal=database-url="postgresql://user:pass@host:5432/soundhash" \
  --from-literal=api-secret-key="your-secret-key"
```

### 2. Deploy All Resources

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml
kubectl apply -f service.yaml
kubectl apply -f deployment.yaml
kubectl apply -f hpa.yaml
kubectl apply -f ingress.yaml
kubectl apply -f cert-manager.yaml
kubectl apply -f pgbouncer.yaml
kubectl apply -f redis.yaml
```

### 3. Verify

```bash
kubectl get all -n soundhash-production
```

## Using Helm Instead

For a better deployment experience, use Helm:

```bash
helm install soundhash ../helm/soundhash \
  --namespace soundhash-production \
  --values ../helm/soundhash/values-production.yaml
```

See [../helm/soundhash/](../helm/soundhash/) for Helm charts.

## Documentation

See [../docs/deployment/kubernetes.md](../docs/deployment/kubernetes.md) for detailed documentation.

## Important Notes

- Never commit `secrets.yaml` - use the template
- Update hostnames in `ingress.yaml` for your domain
- Configure storage classes for your cluster
- Adjust resource limits based on workload
- Enable cert-manager before deploying ingress

## Prerequisites

- Kubernetes cluster v1.27+
- kubectl configured
- Storage classes available (gp3, efs-sc)
- nginx-ingress controller installed
- cert-manager installed (for TLS)
