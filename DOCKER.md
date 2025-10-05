# Docker Deployment Guide

## Architecture

The SoundHash Docker setup consists of multiple services:

-   **postgres**: PostgreSQL database (port 5433)
-   **soundhash_app**: Main application container
-   **soundhash_ingestion**: Channel processing service
-   **soundhash_twitter_bot**: Twitter bot service
-   **soundhash_setup**: Database initialization service

## Service Profiles

Services are organized using Docker Compose profiles:

-   **Default**: `postgres`, `soundhash_app` (core services)
-   **setup**: `soundhash_setup` (database initialization)
-   **ingestion**: `soundhash_ingestion` (channel processing)
-   **bots**: `soundhash_twitter_bot` (social media bots)

## Port Configuration

-   PostgreSQL: **5433** (external) → 5432 (internal)
-   Application: 8000 (reserved for future web interface)

The external PostgreSQL port (5433) is specifically chosen to avoid conflicts with existing PostgreSQL installations running on the standard port 5432.

## Volume Mounts

-   `postgres_data`: Persistent PostgreSQL data
-   `./temp:/app/temp`: Temporary files (audio processing)
-   `./logs:/app/logs`: Application logs

## Environment Variables

### Required API Keys (.env.docker)

```env
# YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key_here

# Twitter API
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
TWITTER_CONSUMER_KEY=your_twitter_consumer_key_here
TWITTER_CONSUMER_SECRET=your_twitter_consumer_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# Reddit API (optional)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
```

### Database Configuration (automatic)

```env
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=soundhash
DATABASE_USER=soundhash_user
DATABASE_PASSWORD=soundhash_password123
```

## Network Configuration

All services run on a custom bridge network (`soundhash_network`) for secure inter-service communication.

## Health Checks

PostgreSQL includes health checks to ensure the database is ready before dependent services start.

## Data Persistence

-   Database data persists in the `postgres_data` Docker volume
-   Temporary files are stored in `./temp` (mounted from host)
-   Logs are stored in `./logs` (mounted from host)

## Scaling Considerations

-   Increase PostgreSQL memory limits for large datasets
-   Use separate containers for different bot platforms
-   Consider Redis for caching in high-load scenarios
-   Monitor temp directory disk usage during processing

## Security Notes

-   Database password is hardcoded for development
-   Change credentials for production deployment
-   API keys are loaded from environment file
-   Container runs as non-root user (soundhash:1000)

## Troubleshooting

### Common Issues

**Port 5433 already in use:**

```bash
# Check what's using the port
sudo lsof -i :5433

# Change port in docker-compose.yml if needed
```

**Container startup failures:**

```bash
# Check service logs
./docker/manage.sh logs postgres
./docker/manage.sh logs soundhash_app

# Check service status
./docker/manage.sh status
```

**Database connection issues:**

```bash
# Test database connectivity
docker-compose exec postgres psql -U soundhash_user -d soundhash

# Check database logs
./docker/manage.sh logs postgres
```

**Out of disk space:**

```bash
# Clean up temp files
docker-compose exec soundhash_app rm -rf /app/temp/*

# Clean up Docker images
docker system prune -f
```

### Performance Tuning

**PostgreSQL Configuration:**

-   The init script optimizes PostgreSQL for audio fingerprinting workloads
-   Increase `shared_buffers` and `effective_cache_size` for large datasets
-   Monitor query performance with `EXPLAIN ANALYZE`

**Processing Configuration:**

-   Adjust `MAX_CONCURRENT_DOWNLOADS` based on available bandwidth
-   Tune `SEGMENT_LENGTH_SECONDS` for your use case
-   Monitor memory usage during fingerprint extraction

## Production Deployment

For production deployment, consider:

1. **Use Docker Swarm or Kubernetes** for orchestration
2. **External PostgreSQL** for better performance and backup
3. **Load balancing** for multiple bot instances
4. **Monitoring** with Prometheus/Grafana
5. **Log aggregation** with ELK stack
6. **Secrets management** instead of environment files
7. **SSL/TLS** termination with reverse proxy
