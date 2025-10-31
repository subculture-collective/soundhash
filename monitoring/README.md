# SoundHash Monitoring Configuration

This directory contains configuration files for the SoundHash monitoring stack.

## Directory Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml       # Prometheus scrape configuration
│   └── alerts.yml          # Alert rules
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/    # Datasource configuration
│   │   └── dashboards/     # Dashboard provisioning
│   └── dashboards/         # Dashboard JSON files
├── loki/
│   └── loki-config.yml     # Loki configuration
├── promtail/
│   └── promtail-config.yml # Promtail configuration
└── alertmanager/
    └── alertmanager.yml    # AlertManager routing configuration
```

## Components

### Prometheus

**Purpose**: Time-series database for metrics collection

**Configuration**: `prometheus/prometheus.yml`
- Scrape interval: 15s
- Retention: 30 days
- Targets: SoundHash app, Postgres, Redis, Node Exporter

**Alert Rules**: `prometheus/alerts.yml`
- Application alerts (errors, performance)
- System alerts (CPU, memory, disk)
- Database alerts
- SLA alerts

**Access**: http://localhost:9091

### Grafana

**Purpose**: Metrics visualization and dashboards

**Configuration**: 
- Datasources: `grafana/provisioning/datasources/datasources.yml`
- Dashboards: `grafana/provisioning/dashboards/dashboards.yml`

**Dashboards**:
- `soundhash-overview.json`: Main application dashboard

**Access**: http://localhost:3001 (admin/admin)

### Jaeger

**Purpose**: Distributed tracing

**Features**:
- OpenTelemetry support
- OTLP gRPC/HTTP receivers
- Prometheus metrics integration

**Access**: http://localhost:16686

### Loki

**Purpose**: Log aggregation

**Configuration**: `loki/loki-config.yml`
- Retention: 31 days
- Storage: Local filesystem (use S3/GCS for production)

**Access**: http://localhost:3100 (via Grafana)

### Promtail

**Purpose**: Log shipping to Loki

**Configuration**: `promtail/promtail-config.yml`
- Collects application logs
- Collects Docker container logs
- JSON log parsing

### AlertManager

**Purpose**: Alert routing and management

**Configuration**: `alertmanager/alertmanager.yml`
- Slack notifications
- Discord notifications
- PagerDuty integration (optional)
- Alert grouping and deduplication

**Access**: http://localhost:9093

## Quick Start

1. **Start monitoring stack**:
   ```bash
   # Option 1: Monitoring stack only (without postgres-exporter)
   docker compose -f docker-compose.monitoring.yml up -d
   
   # Option 2: Full stack with application and database monitoring
   docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
   ```

2. **Verify services**:
   ```bash
   docker compose ps
   ```

3. **Access UIs**:
   - Grafana: http://localhost:3001
   - Prometheus: http://localhost:9091
   - Jaeger: http://localhost:16686
   - AlertManager: http://localhost:9093

**Note**: The `postgres-exporter` service requires the main `docker-compose.yml` to be used together with `docker-compose.monitoring.yml`. If you only want to run the monitoring stack standalone, it will skip the postgres-exporter automatically.

## Customization

### Adding New Dashboards

1. Create dashboard in Grafana UI
2. Export JSON
3. Save to `grafana/dashboards/`
4. Dashboard will auto-load on restart

### Modifying Alert Rules

1. Edit `prometheus/alerts.yml`
2. Reload Prometheus:
   ```bash
   curl -X POST http://localhost:9091/-/reload
   ```

### Configuring Alert Notifications

1. Edit `alertmanager/alertmanager.yml`
2. Add webhook URLs for Slack/Discord
3. Configure PagerDuty integration
4. Restart AlertManager:
   ```bash
   docker compose restart alertmanager
   ```

## Production Considerations

### Persistence

All monitoring data is stored in Docker volumes:
- `prometheus_data`: Metrics data
- `grafana_data`: Dashboards and settings
- `loki_data`: Log data
- `alertmanager_data`: AlertManager state

### Backup

Backup these volumes regularly:
```bash
docker run --rm -v soundhash-prometheus-data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data
```

### Resource Requirements

Minimum recommended resources:
- Prometheus: 2GB RAM, 50GB disk
- Grafana: 512MB RAM, 10GB disk
- Loki: 1GB RAM, 100GB disk
- Jaeger: 512MB RAM, 20GB disk

### High Availability

For production:
1. Run multiple Prometheus instances with federation
2. Use external PostgreSQL for Grafana
3. Configure Loki with object storage (S3/GCS)
4. Deploy Jaeger with Elasticsearch backend

## Monitoring the Monitors

The monitoring stack itself is monitored:
- Prometheus monitors its own health
- Node Exporter provides system metrics
- Each component has health checks
- AlertManager can alert on monitoring failures

## Troubleshooting

### Services Not Starting

Check logs:
```bash
docker compose logs prometheus
docker compose logs grafana
docker compose logs loki
```

### High Resource Usage

1. Reduce Prometheus retention:
   Edit `prometheus.yml`: `--storage.tsdb.retention.time=15d`

2. Reduce Loki retention:
   Edit `loki-config.yml`: `retention_period: 360h`

3. Increase trace sampling:
   Edit `.env`: `SENTRY_TRACES_SAMPLE_RATE=0.01`

### Alerts Not Firing

1. Check alert rules are loaded:
   http://localhost:9091/alerts

2. Verify AlertManager configuration:
   http://localhost:9093/#/status

3. Test alert delivery:
   ```bash
   curl -X POST http://localhost:9093/api/v1/alerts -d '[{"labels":{"alertname":"test"}}]'
   ```

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [SoundHash Monitoring Guide](../docs/MONITORING.md)
