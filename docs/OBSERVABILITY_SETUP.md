# Observability Setup Guide

Quick setup guide for SoundHash monitoring, tracing, and logging.

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Access to create environment variables

## Quick Start (5 minutes)

### 1. Enable Basic Metrics

Add to your `.env` file:

```env
METRICS_ENABLED=true
METRICS_PORT=9090
```

Start your application:
```bash
python scripts/your_script.py
```

View metrics: http://localhost:9090/metrics

### 2. Start Monitoring Stack

```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

Wait 30 seconds for services to start, then access:
- **Grafana**: http://localhost:3001 (login: admin/admin)
- **Prometheus**: http://localhost:9091
- **Jaeger**: http://localhost:16686

### 3. View Your First Dashboard

1. Open Grafana: http://localhost:3001
2. Navigate to Dashboards → SoundHash → Overview
3. You should see real-time metrics!

## Optional: Enable Tracing

Add to `.env`:
```env
TRACING_ENABLED=true
JAEGER_ENABLED=true
JAEGER_AGENT_HOST=jaeger
```

Restart your application and visit Jaeger: http://localhost:16686

## Optional: Enable Error Tracking

1. Sign up for Sentry: https://sentry.io
2. Create a project and get your DSN
3. Add to `.env`:
   ```env
   SENTRY_ENABLED=true
   SENTRY_DSN=https://your-key@sentry.io/project-id
   ```

## Optional: Enable Structured Logging

Add to `.env`:
```env
STRUCTURED_LOGGING_ENABLED=true
LOG_FORMAT=json
```

Logs will be in JSON format, perfect for Loki/ELK.

## Troubleshooting

### Monitoring stack won't start

```bash
# Check what's running
docker compose ps

# Check logs
docker compose logs prometheus
docker compose logs grafana
```

### Can't access Grafana

1. Wait 30 seconds after starting
2. Check it's running: `docker compose ps grafana`
3. Try: http://localhost:3001

### No metrics showing

1. Verify metrics endpoint: http://localhost:9090/metrics
2. Check Prometheus targets: http://localhost:9091/targets
3. Verify `METRICS_ENABLED=true` in `.env`

## What's Next?

- Read the full guide: [MONITORING.md](./MONITORING.md)
- Set up alerts: Edit `monitoring/prometheus/alerts.yml`
- Customize dashboards: Open Grafana and edit dashboards
- Deploy to production: See Kubernetes manifests in `k8s/`

## Configuration Reference

### Metrics
- `METRICS_ENABLED`: Enable Prometheus metrics (default: true)
- `METRICS_PORT`: Port for metrics endpoint (default: 9090)

### Tracing
- `TRACING_ENABLED`: Enable distributed tracing (default: false)
- `JAEGER_ENABLED`: Enable Jaeger exporter (default: false)
- `JAEGER_AGENT_HOST`: Jaeger host (default: localhost)
- `JAEGER_AGENT_PORT`: Jaeger port (default: 6831)

### Error Tracking
- `SENTRY_ENABLED`: Enable Sentry (default: false)
- `SENTRY_DSN`: Your Sentry project DSN
- `SENTRY_ENVIRONMENT`: Environment name (default: development)
- `SENTRY_TRACES_SAMPLE_RATE`: % of traces to send (default: 0.1)

### Logging
- `STRUCTURED_LOGGING_ENABLED`: Enable JSON logs (default: false)
- `LOG_FORMAT`: text or json (default: text)
- `LOG_OUTPUT`: stdout, file, or both (default: stdout)

## Support

- Full documentation: [MONITORING.md](./MONITORING.md)
- GitHub Issues: https://github.com/subculture-collective/soundhash/issues
