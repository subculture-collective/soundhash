# Kubernetes Deployment Troubleshooting Guide

This guide helps you diagnose and fix common issues with SoundHash Kubernetes deployment.

## Table of Contents

- [Pod Issues](#pod-issues)
- [Networking Issues](#networking-issues)
- [Storage Issues](#storage-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [Security Issues](#security-issues)

## Pod Issues

### Pods are Pending

**Symptoms**: Pods stuck in `Pending` state

**Diagnosis**:
```bash
kubectl describe pod <pod-name> -n soundhash-production
```

**Common Causes**:

1. **Insufficient Resources**
   ```bash
   # Check node resources
   kubectl top nodes
   kubectl describe nodes
   ```
   
   **Solution**: Scale up cluster or reduce resource requests

2. **PVC Not Bound**
   ```bash
   kubectl get pvc -n soundhash-production
   ```
   
   **Solution**: Check storage class availability and provisioner

3. **Node Selector Mismatch**
   ```bash
   kubectl get nodes --show-labels
   ```
   
   **Solution**: Update nodeSelector in values.yaml or add labels to nodes

### Pods are CrashLoopBackOff

**Symptoms**: Pods repeatedly restarting

**Diagnosis**:
```bash
# View current logs
kubectl logs <pod-name> -n soundhash-production

# View previous crash logs
kubectl logs <pod-name> -n soundhash-production --previous
```

**Common Causes**:

1. **Database Connection Failed**
   ```bash
   # Check database secret
   kubectl get secret soundhash-secrets -n soundhash-production -o yaml
   
   # Test database connectivity
   kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
     psql $DATABASE_URL
   ```

2. **Missing Environment Variables**
   ```bash
   kubectl describe pod <pod-name> -n soundhash-production | grep -A 20 "Environment:"
   ```
   
   **Solution**: Update ConfigMap or Secrets

3. **Port Already in Use**
   Check if another process is using port 8000

4. **Failed Health Check**
   ```bash
   kubectl describe pod <pod-name> -n soundhash-production | grep -A 10 "Liveness:"
   ```
   
   **Solution**: Increase `initialDelaySeconds` or `timeoutSeconds`

### Pods are ImagePullBackOff

**Symptoms**: Cannot pull container image

**Diagnosis**:
```bash
kubectl describe pod <pod-name> -n soundhash-production | grep -A 10 "Events:"
```

**Common Causes**:

1. **Image Does Not Exist**
   ```bash
   docker pull ghcr.io/subculture-collective/soundhash:latest
   ```

2. **No Image Pull Secret**
   ```bash
   kubectl get secrets -n soundhash-production
   
   # Create image pull secret
   kubectl create secret docker-registry ghcr-secret \
     --docker-server=ghcr.io \
     --docker-username=$GITHUB_USERNAME \
     --docker-password=$GITHUB_TOKEN \
     -n soundhash-production
   
   # Update deployment
   kubectl patch serviceaccount soundhash-api \
     -n soundhash-production \
     -p '{"imagePullSecrets": [{"name": "ghcr-secret"}]}'
   ```

3. **Rate Limiting**
   Wait and retry, or use authenticated pulls

## Networking Issues

### Cannot Access Service

**Diagnosis**:
```bash
# Check service
kubectl get svc soundhash-api-service -n soundhash-production

# Check endpoints
kubectl get endpoints soundhash-api-service -n soundhash-production

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://soundhash-api-service.soundhash-production.svc.cluster.local/health
```

**Solutions**:

1. **Service selector mismatch**
   ```bash
   kubectl get pods -n soundhash-production --show-labels
   kubectl get svc soundhash-api-service -n soundhash-production -o yaml | grep selector -A 5
   ```

2. **Load Balancer not provisioned**
   ```bash
   kubectl describe svc soundhash-api-service -n soundhash-production
   ```
   
   Check cloud provider configuration

### Ingress Not Working

**Diagnosis**:
```bash
kubectl get ingress -n soundhash-production
kubectl describe ingress soundhash-ingress -n soundhash-production
```

**Common Issues**:

1. **Ingress Controller Not Installed**
   ```bash
   kubectl get pods -n ingress-nginx
   
   # Install if missing
   helm install ingress-nginx ingress-nginx/ingress-nginx \
     --namespace ingress-nginx \
     --create-namespace
   ```

2. **SSL Certificate Not Issued**
   ```bash
   kubectl get certificate -n soundhash-production
   kubectl describe certificate soundhash-tls -n soundhash-production
   
   # Check cert-manager
   kubectl get pods -n cert-manager
   kubectl logs -n cert-manager deployment/cert-manager
   ```

3. **DNS Not Resolving**
   ```bash
   dig api.soundhash.io
   nslookup api.soundhash.io
   ```

## Storage Issues

### PVC Not Binding

**Diagnosis**:
```bash
kubectl get pvc -n soundhash-production
kubectl describe pvc <pvc-name> -n soundhash-production
```

**Solutions**:

1. **Storage Class Not Available**
   ```bash
   kubectl get storageclass
   
   # Check if efs-sc exists
   kubectl get storageclass efs-sc
   ```
   
   Update storage class in values.yaml if needed

2. **No Available Volumes**
   Check cloud provider quotas and provisioner logs

3. **Access Mode Mismatch**
   Change `ReadWriteMany` to `ReadWriteOnce` if EFS is not available

### Disk Space Issues

**Diagnosis**:
```bash
# Check disk usage in pods
kubectl exec -n soundhash-production <pod-name> -- df -h

# Check PVC usage
kubectl exec -n soundhash-production <pod-name> -- du -sh /app/temp /app/cache /app/logs
```

**Solutions**:

1. **Resize PVC**
   ```bash
   kubectl patch pvc soundhash-temp-pvc -n soundhash-production \
     -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
   ```

2. **Clean up temporary files**
   ```bash
   kubectl exec -n soundhash-production <pod-name> -- find /app/temp -type f -mtime +7 -delete
   ```

## Database Issues

### Connection Pool Exhausted

**Symptoms**: "Too many connections" errors

**Diagnosis**:
```bash
# Check PgBouncer
kubectl get pods -n soundhash-production -l app=pgbouncer
kubectl logs -n soundhash-production -l app=pgbouncer

# Check database connections
kubectl exec -n soundhash-production <pod-name> -- \
  psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
```

**Solutions**:

1. **Increase Pool Size**
   Edit `k8s/pgbouncer.yaml`:
   ```yaml
   default_pool_size = 50  # Increase from 25
   max_client_conn = 2000  # Increase from 1000
   ```

2. **Scale PgBouncer**
   ```bash
   kubectl scale deployment/pgbouncer -n soundhash-production --replicas=4
   ```

### Slow Queries

**Diagnosis**:
```bash
# Enable query logging in RDS
# Check slow query log

# Check PostgreSQL stats
kubectl exec -n soundhash-production <pod-name> -- \
  psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

**Solutions**:

1. Add database indexes
2. Optimize query patterns
3. Increase database instance size
4. Enable connection pooling with PgBouncer

## Performance Issues

### High CPU Usage

**Diagnosis**:
```bash
# Check pod CPU
kubectl top pods -n soundhash-production

# Check HPA status
kubectl get hpa -n soundhash-production
kubectl describe hpa soundhash-api-hpa -n soundhash-production
```

**Solutions**:

1. **Scale Horizontally**
   ```bash
   # Manual scaling
   kubectl scale deployment/soundhash-api -n soundhash-production --replicas=10
   
   # Adjust HPA
   kubectl patch hpa soundhash-api-hpa -n soundhash-production \
     -p '{"spec":{"maxReplicas":30}}'
   ```

2. **Increase CPU Limits**
   Edit `helm/soundhash/values-production.yaml`:
   ```yaml
   resources:
     limits:
       cpu: "2000m"  # Increase from 1000m
   ```

### High Memory Usage

**Diagnosis**:
```bash
kubectl top pods -n soundhash-production

# Memory usage details
kubectl exec -n soundhash-production <pod-name> -- ps aux --sort=-%mem | head
```

**Solutions**:

1. **Increase Memory Limits**
   ```yaml
   resources:
     limits:
       memory: "4Gi"  # Increase from 2Gi
   ```

2. **Check for Memory Leaks**
   - Profile application
   - Check for unclosed database connections
   - Review cache size settings

### Slow Response Times

**Diagnosis**:
```bash
# Test endpoint response time
time curl https://api.soundhash.io/health

# Check pod logs for slow requests
kubectl logs -n soundhash-production <pod-name> | grep -i "slow\|timeout"
```

**Solutions**:

1. Enable Redis caching
2. Add database indexes
3. Optimize API queries
4. Use connection pooling
5. Add CDN for static content

## Security Issues

### Pod Security Policy Violations

**Diagnosis**:
```bash
kubectl describe pod <pod-name> -n soundhash-production | grep -i "security\|policy"
```

**Solutions**:

1. **Running as Root**
   Ensure security context is set:
   ```yaml
   securityContext:
     runAsNonRoot: true
     runAsUser: 1000
   ```

2. **Privileged Container**
   Remove privileged flag or add proper capabilities

### Secrets Exposed

**Prevention**:

1. **Never commit secrets to Git**
   ```bash
   git log --all --full-history -- "*secret*"
   ```

2. **Use External Secrets Manager**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Sealed Secrets

3. **Rotate Secrets Regularly**
   ```bash
   kubectl delete secret soundhash-secrets -n soundhash-production
   kubectl create secret generic soundhash-secrets \
     --from-literal=api-secret-key="NEW_KEY" \
     -n soundhash-production
   
   # Restart pods to pick up new secrets
   kubectl rollout restart deployment/soundhash-api -n soundhash-production
   ```

## Useful Debug Commands

### General Debugging

```bash
# Get all resources
kubectl get all -n soundhash-production

# Describe resource
kubectl describe <resource-type> <resource-name> -n soundhash-production

# View events
kubectl get events -n soundhash-production --sort-by='.lastTimestamp'

# Check resource quotas
kubectl describe resourcequota -n soundhash-production

# Check limit ranges
kubectl describe limitrange -n soundhash-production
```

### Pod Debugging

```bash
# Shell into pod
kubectl exec -it -n soundhash-production <pod-name> -- /bin/bash

# Run command in pod
kubectl exec -n soundhash-production <pod-name> -- <command>

# Copy files from pod
kubectl cp soundhash-production/<pod-name>:/app/logs/app.log ./app.log

# View pod YAML
kubectl get pod <pod-name> -n soundhash-production -o yaml
```

### Network Debugging

```bash
# Test DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup soundhash-api-service.soundhash-production.svc.cluster.local

# Test connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl -v http://soundhash-api-service.soundhash-production.svc.cluster.local/health

# Check network policies
kubectl get networkpolicies -n soundhash-production
```

## Getting More Help

1. **Check Logs**: Always start with application logs
2. **Search Issues**: Check GitHub issues for similar problems
3. **Community**: Ask in project discussions
4. **Documentation**: Review Kubernetes and application docs
5. **Professional Support**: Contact maintainers for enterprise support

## Preventive Measures

1. **Monitoring**: Set up Prometheus + Grafana
2. **Alerting**: Configure alerts for critical metrics
3. **Logging**: Use centralized logging (ELK/Loki)
4. **Testing**: Regular load testing
5. **Backups**: Automated database backups
6. **Disaster Recovery**: Test recovery procedures
7. **Documentation**: Keep runbooks updated
8. **Training**: Ensure team knows common issues

---

**Still having issues?** Open a [GitHub issue](https://github.com/subculture-collective/soundhash/issues) with:
- Problem description
- Error messages
- Output of relevant `kubectl` commands
- Environment details (K8s version, cloud provider)
