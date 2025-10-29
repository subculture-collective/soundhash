# Quick Start - Production Deployment

This guide will help you deploy SoundHash to production in 30 minutes.

## Prerequisites Checklist

- [ ] Kubernetes cluster (v1.27+) is running
- [ ] kubectl installed and configured
- [ ] Helm 3.x installed
- [ ] Docker installed
- [ ] Access to container registry (ghcr.io)
- [ ] Domain name configured (optional)

## Step 1: Clone Repository (2 min)

```bash
git clone https://github.com/subculture-collective/soundhash.git
cd soundhash
```

## Step 2: Build and Push Docker Image (5 min)

```bash
# Build production image
docker build -t ghcr.io/YOUR_ORG/soundhash:v1.0.0 -f Dockerfile.production .

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Push image
docker push ghcr.io/YOUR_ORG/soundhash:v1.0.0
```

## Step 3: Create Secrets (3 min)

```bash
# Create production namespace
kubectl create namespace soundhash-production

# Create secrets
kubectl create secret generic soundhash-secrets \
  --namespace=soundhash-production \
  --from-literal=database-url="postgresql://user:password@db-host:5432/soundhash" \
  --from-literal=database-user="soundhash_user" \
  --from-literal=database-password="STRONG_PASSWORD" \
  --from-literal=database-name="soundhash" \
  --from-literal=api-secret-key="RANDOM_SECRET_KEY_MIN_32_CHARS" \
  --from-literal=youtube-api-key="YOUR_YOUTUBE_KEY"
```

**Security Note**: In production, use a secrets manager like:
- AWS Secrets Manager
- HashiCorp Vault
- Sealed Secrets

## Step 4: Configure Values (5 min)

Edit `helm/soundhash/values-production.yaml`:

```yaml
image:
  repository: ghcr.io/YOUR_ORG/soundhash
  tag: "v1.0.0"

ingress:
  enabled: true
  hosts:
    - host: api.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: soundhash-tls
      hosts:
        - api.yourdomain.com

postgresql:
  external:
    host: your-rds-endpoint.amazonaws.com
    port: 5432
```

## Step 5: Install Dependencies (5 min)

### Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### Install cert-manager (for SSL)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=Available --timeout=300s \
  deployment/cert-manager -n cert-manager
```

## Step 6: Deploy SoundHash (5 min)

```bash
# Deploy with Helm
helm install soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --values ./helm/soundhash/values-production.yaml \
  --wait \
  --timeout 10m
```

## Step 7: Verify Deployment (5 min)

```bash
# Check pods
kubectl get pods -n soundhash-production

# Check services
kubectl get svc -n soundhash-production

# Check ingress
kubectl get ingress -n soundhash-production

# View logs
kubectl logs -f -n soundhash-production -l app.kubernetes.io/name=soundhash
```

Expected output:
```
NAME                            READY   STATUS    RESTARTS   AGE
soundhash-api-xxxxxxxxxx-xxxxx  1/1     Running   0          2m
soundhash-api-xxxxxxxxxx-xxxxx  1/1     Running   0          2m
soundhash-api-xxxxxxxxxx-xxxxx  1/1     Running   0          2m
```

## Step 8: Test Endpoints

```bash
# Get the load balancer IP/hostname
LB_URL=$(kubectl get svc soundhash-api-service -n soundhash-production \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health endpoint
curl http://$LB_URL/health

# Expected: {"status":"healthy","database":"connected"}
```

If using ingress with domain:
```bash
curl https://api.yourdomain.com/health
curl https://api.yourdomain.com/health/ready
```

## Step 9: Configure DNS (if using ingress)

Point your domain to the Load Balancer:

```bash
# Get load balancer hostname
kubectl get ingress soundhash-ingress -n soundhash-production

# Create DNS A or CNAME record:
# api.yourdomain.com -> [Load Balancer DNS]
```

## Step 10: Run Database Migrations

```bash
POD_NAME=$(kubectl get pods -n soundhash-production \
  -l app.kubernetes.io/name=soundhash,component=api \
  -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n soundhash-production $POD_NAME -- alembic upgrade head
```

## Verification Checklist

- [ ] All pods are running (3 replicas)
- [ ] Health endpoint returns 200 OK
- [ ] Readiness endpoint returns 200 OK
- [ ] Database connection is working
- [ ] SSL certificate is issued (if using cert-manager)
- [ ] DNS is resolving correctly
- [ ] Logs show no errors

## Common Issues

### Pods are in ImagePullBackOff
```bash
# Check image pull secrets
kubectl get secrets -n soundhash-production
kubectl describe pod <pod-name> -n soundhash-production
```

### Database connection fails
```bash
# Check secrets
kubectl get secret soundhash-secrets -n soundhash-production -o yaml

# Test database connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql postgresql://user:pass@host:5432/soundhash
```

### SSL certificate not issued
```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Check certificate status
kubectl describe certificate soundhash-tls -n soundhash-production
```

## Monitoring and Maintenance

### View Application Logs
```bash
kubectl logs -f -n soundhash-production -l app.kubernetes.io/name=soundhash
```

### Check Resource Usage
```bash
kubectl top pods -n soundhash-production
kubectl top nodes
```

### Scale Manually
```bash
kubectl scale deployment/soundhash-api -n soundhash-production --replicas=5
```

### Check Autoscaler
```bash
kubectl get hpa -n soundhash-production
kubectl describe hpa soundhash-api-hpa -n soundhash-production
```

## Next Steps

1. **Set up monitoring**: Deploy Prometheus and Grafana
2. **Configure alerts**: Set up alerting for critical metrics
3. **Enable log aggregation**: Deploy ELK or Loki
4. **Set up backups**: Configure database backups
5. **Configure CI/CD**: Set up GitHub Actions workflows
6. **Load testing**: Validate autoscaling behavior
7. **Security audit**: Review and harden security settings

## Getting Help

- **Documentation**: [Full Kubernetes Guide](./kubernetes.md)
- **Issues**: [GitHub Issues](https://github.com/subculture-collective/soundhash/issues)
- **Helm Chart**: [Helm Guide](./helm.md)
- **Infrastructure**: [Terraform Guide](./terraform.md)

## Useful Commands

```bash
# Update deployment
helm upgrade soundhash ./helm/soundhash \
  --namespace soundhash-production \
  --values ./helm/soundhash/values-production.yaml

# Rollback
helm rollback soundhash --namespace soundhash-production

# Uninstall
helm uninstall soundhash --namespace soundhash-production

# Port forward for local testing
kubectl port-forward -n soundhash-production svc/soundhash-api-service 8000:80

# Shell into pod
kubectl exec -it -n soundhash-production <pod-name> -- /bin/bash
```

## Production Checklist

Before going live:

- [ ] Secrets are stored securely (not in ConfigMaps)
- [ ] Resource limits are set appropriately
- [ ] Monitoring and alerting are configured
- [ ] Backups are automated and tested
- [ ] Disaster recovery plan is documented
- [ ] Security best practices are followed
- [ ] Load testing is completed
- [ ] Runbooks are created for common operations
- [ ] On-call rotation is established
- [ ] Cost alerts are configured

## Estimated Timeline

- **Basic Setup**: 30 minutes (following this guide)
- **With Terraform**: 1-2 hours (infrastructure provisioning)
- **Full Production Setup**: 4-8 hours (including monitoring, security, backups)

---

**Need help?** Open an issue or check the [full documentation](./kubernetes.md).
