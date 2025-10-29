# Kubernetes Deployment Guide

This guide covers deploying SoundHash to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.27+)
- kubectl configured to access your cluster
- Helm 3.x installed
- Docker installed (for building images)
- Access to push images to ghcr.io/subculture-collective/soundhash

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build production image
docker build -t ghcr.io/subculture-collective/soundhash:latest -f Dockerfile.production .

# Push to registry
docker push ghcr.io/subculture-collective/soundhash:latest
```

### 2. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 3. Create Secrets

```bash
# Create secrets from literals
kubectl create secret generic soundhash-secrets \
  --namespace=soundhash-production \
  --from-literal=database-url="postgresql://user:pass@host:5432/soundhash" \
  --from-literal=database-user="soundhash_user" \
  --from-literal=database-password="your-password" \
  --from-literal=database-name="soundhash" \
  --from-literal=api-secret-key="your-secret-key" \
  --from-literal=youtube-api-key="your-youtube-key"
```

Or use a secrets management tool like:
- AWS Secrets Manager with External Secrets Operator
- HashiCorp Vault
- Sealed Secrets

### 4. Deploy with kubectl

```bash
# Apply all configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/hpa.yaml

# Deploy ingress (requires ingress-nginx)
kubectl apply -f k8s/ingress.yaml

# Deploy cert-manager for SSL (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
kubectl apply -f k8s/cert-manager.yaml

# Deploy PgBouncer (optional but recommended)
kubectl apply -f k8s/pgbouncer.yaml

# Deploy Redis
kubectl apply -f k8s/redis.yaml
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n soundhash-production

# Check services
kubectl get svc -n soundhash-production

# Check ingress
kubectl get ingress -n soundhash-production

# View logs
kubectl logs -f -n soundhash-production -l app=soundhash,component=api
```

## Components

### API Deployment
- **Replicas**: 3 (scales 3-20 with HPA)
- **Resources**: 512Mi-2Gi memory, 250m-1000m CPU
- **Probes**: Liveness, readiness, and startup probes configured
- **Security**: Non-root user, dropped capabilities, read-only root filesystem where possible

### Persistent Storage
- **Temp Storage**: 50Gi (ReadWriteMany via EFS)
- **Cache Storage**: 20Gi (ReadWriteMany via EFS)
- **Logs Storage**: 10Gi (ReadWriteMany via EFS)

### Autoscaling
- **CPU Target**: 70%
- **Memory Target**: 80%
- **Scale Down**: Max 50% every 60s after 5min stabilization
- **Scale Up**: Max 100% or 4 pods every 30s

### Ingress
- **Controller**: nginx-ingress
- **TLS**: Let's Encrypt via cert-manager
- **Rate Limiting**: 100 requests/minute, 10 RPS
- **WebSocket**: Supported

### PgBouncer (Connection Pooling)
- **Pool Mode**: Transaction
- **Max Connections**: 1000
- **Pool Size**: 25 per connection
- **Replicas**: 2

### Redis
- **Type**: StatefulSet
- **Replicas**: 3
- **Storage**: 10Gi per replica
- **Persistence**: Enabled with RDB and AOF

## Health Checks

The application exposes two health endpoints:

- **`/health`**: Basic health check (database connectivity)
- **`/health/ready`**: Readiness check (database + Redis if enabled)

Kubernetes probes use these endpoints to manage pod lifecycle.

## Monitoring

Pods are annotated for Prometheus scraping:
```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "8000"
prometheus.io/path: "/metrics"
```

## Scaling

### Manual Scaling
```bash
kubectl scale deployment/soundhash-api -n soundhash-production --replicas=5
```

### Autoscaling
HPA automatically scales based on CPU and memory utilization.

## Rolling Updates

The deployment uses a RollingUpdate strategy with:
- **Max Surge**: 1 (one extra pod during update)
- **Max Unavailable**: 0 (zero-downtime deployments)

Update the image:
```bash
kubectl set image deployment/soundhash-api \
  -n soundhash-production \
  api=ghcr.io/subculture-collective/soundhash:v2.0.0
```

## Rollback

```bash
# View rollout history
kubectl rollout history deployment/soundhash-api -n soundhash-production

# Rollback to previous version
kubectl rollout undo deployment/soundhash-api -n soundhash-production

# Rollback to specific revision
kubectl rollout undo deployment/soundhash-api -n soundhash-production --to-revision=2
```

## Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod <pod-name> -n soundhash-production
kubectl logs <pod-name> -n soundhash-production
```

### Database Connection Issues
```bash
# Check database connectivity from pod
kubectl exec -it <pod-name> -n soundhash-production -- psql $DATABASE_URL -c "SELECT 1"
```

### Check HPA Status
```bash
kubectl get hpa -n soundhash-production
kubectl describe hpa soundhash-api-hpa -n soundhash-production
```

### View Events
```bash
kubectl get events -n soundhash-production --sort-by='.lastTimestamp'
```

## Security Best Practices

1. **Use Secrets Management**: Don't store secrets in ConfigMaps
2. **RBAC**: Configure proper Role-Based Access Control
3. **Network Policies**: Implement network segmentation
4. **Pod Security**: Use security contexts and pod security standards
5. **Image Scanning**: Scan images for vulnerabilities
6. **Resource Limits**: Always set resource requests and limits
7. **TLS Everywhere**: Use TLS for all external and internal communication

## Using Helm

See [helm.md](./helm.md) for deploying with Helm charts.

## Infrastructure as Code

See [terraform.md](./terraform.md) for provisioning infrastructure with Terraform.

## Next Steps

- Set up monitoring with Prometheus and Grafana
- Configure log aggregation with ELK or Loki
- Implement disaster recovery procedures
- Set up multi-region deployment
- Configure backup and restore procedures