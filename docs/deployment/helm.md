# Helm Deployment Guide

This guide covers deploying SoundHash using Helm charts.

## Prerequisites

- Kubernetes cluster (v1.27+)
- Helm 3.x installed
- kubectl configured to access your cluster

## Installation

### 1. Add Required Helm Repositories

```bash
# Add nginx-ingress
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
```

### 2. Install Dependencies

#### Install NGINX Ingress Controller

```bash
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

#### Install cert-manager (for TLS certificates)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### 3. Create Secrets

```bash
# Create namespace
kubectl create namespace soundhash-production

# Create secrets
kubectl create secret generic soundhash-secrets \
  --namespace=soundhash-production \
  --from-literal=database-url="postgresql://user:pass@host:5432/soundhash" \
  --from-literal=database-user="soundhash_user" \
  --from-literal=database-password="your-password" \
  --from-literal=database-name="soundhash" \
  --from-literal=api-secret-key="your-secret-key" \
  --from-literal=youtube-api-key="your-youtube-key"
```

### 4. Install SoundHash

#### Production Deployment

```bash
helm install soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --values ./helm/soundhash/values-production.yaml \
  --wait
```

#### Staging Deployment

```bash
helm install soundhash ./helm/soundhash \
  --namespace soundhash-staging \
  --create-namespace \
  --values ./helm/soundhash/values-staging.yaml \
  --wait
```

## Configuration

### values.yaml Structure

The Helm chart uses three levels of configuration:

1. **values.yaml**: Base configuration with sensible defaults
2. **values-staging.yaml**: Staging environment overrides
3. **values-production.yaml**: Production environment overrides

### Key Configuration Options

#### Image Settings
```yaml
image:
  repository: ghcr.io/subculture-collective/soundhash
  pullPolicy: IfNotPresent
  tag: "latest"
```

#### Replica Count
```yaml
replicaCount: 3
```

#### Autoscaling
```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

#### Resources
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

#### Ingress
```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.soundhash.io
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: soundhash-tls
      hosts:
        - api.soundhash.io
```

#### Persistence
```yaml
persistence:
  enabled: true
  temp:
    size: 50Gi
    storageClass: efs-sc
  cache:
    size: 20Gi
    storageClass: efs-sc
  logs:
    size: 10Gi
    storageClass: efs-sc
```

### Custom Values

You can override any value during installation:

```bash
helm install soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --set replicaCount=5 \
  --set image.tag=v2.0.0 \
  --set autoscaling.maxReplicas=30
```

Or use a custom values file:

```bash
helm install soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --values my-custom-values.yaml
```

## Upgrading

### Upgrade with New Image

```bash
helm upgrade soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --set image.tag=v2.0.0 \
  --wait
```

### Upgrade with Changed Values

```bash
helm upgrade soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --values ./helm/soundhash/values-production.yaml \
  --wait
```

### Force Recreate Pods

```bash
helm upgrade soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --recreate-pods \
  --wait
```

## Rollback

### List Releases

```bash
helm history soundhash --namespace soundhash-production
```

### Rollback to Previous Version

```bash
helm rollback soundhash --namespace soundhash-production
```

### Rollback to Specific Revision

```bash
helm rollback soundhash 3 --namespace soundhash-production
```

## Uninstalling

```bash
helm uninstall soundhash --namespace soundhash-production
```

This will remove all resources created by the chart except for:
- PersistentVolumeClaims (data is preserved)
- Secrets (must be manually deleted)

To completely remove everything:

```bash
# Uninstall the release
helm uninstall soundhash --namespace soundhash-production

# Delete PVCs
kubectl delete pvc --all -n soundhash-production

# Delete secrets
kubectl delete secret soundhash-secrets -n soundhash-production

# Delete namespace
kubectl delete namespace soundhash-production
```

## Debugging

### Check Release Status

```bash
helm status soundhash --namespace soundhash-production
```

### Get Release Values

```bash
helm get values soundhash --namespace soundhash-production
```

### Get All Resources

```bash
helm get manifest soundhash --namespace soundhash-production
```

### Dry Run

Test installation without actually deploying:

```bash
helm install soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --values ./helm/soundhash/values-production.yaml \
  --dry-run \
  --debug
```

### Template Rendering

See what templates will be rendered:

```bash
helm template soundhash ./helm/soundhash \
  --values ./helm/soundhash/values-production.yaml
```

## Using the Deployment Script

A convenience script is provided at `scripts/deploy.sh`:

```bash
# Deploy to production
./scripts/deploy.sh production v1.0.0

# Deploy to staging
./scripts/deploy.sh staging latest
```

The script:
1. Builds and pushes Docker image
2. Creates namespace if needed
3. Deploys with Helm
4. Runs database migrations
5. Verifies deployment
6. Shows deployment information

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Deploy to Production
  run: |
    helm upgrade --install soundhash ./helm/soundhash \
      --namespace soundhash-production \
      --create-namespace \
      --set image.tag=${{ github.sha }} \
      --values ./helm/soundhash/values-production.yaml \
      --wait \
      --timeout 10m
```

## Best Practices

1. **Use Specific Image Tags**: Avoid `latest` in production
2. **Version Control Values**: Keep custom values files in version control
3. **Test in Staging**: Always test changes in staging first
4. **Monitor Deployments**: Watch pod status during upgrades
5. **Backup Before Upgrade**: Backup database before major upgrades
6. **Use Helm Secrets**: For sensitive data, use helm-secrets plugin
7. **Document Changes**: Keep release notes for each deployment

## Troubleshooting

### Release Stuck in Pending

```bash
helm rollback soundhash --namespace soundhash-production
```

### Validation Errors

```bash
helm lint ./helm/soundhash --values ./helm/soundhash/values-production.yaml
```

### Resource Quota Issues

```bash
kubectl describe resourcequota -n soundhash-production
```

## Next Steps

- Set up ArgoCD for GitOps deployment
- Implement blue-green deployments
- Configure Helm hooks for pre/post deployment tasks
- Add custom Helm tests
- Set up Helmfile for multi-environment management
