#!/bin/bash
# Quick start script for SoundHash Docker deployment

set -e

echo "🎵 SoundHash Docker Quick Start"
echo "==============================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env.docker exists
if [ ! -f .env.docker ]; then
    if [ -f .env.docker.example ]; then
        echo "📋 Creating .env.docker from example..."
        cp .env.docker.example .env.docker
        echo "⚠️  Please edit .env.docker with your API keys before proceeding!"
        echo ""
        echo "Required API keys:"
        echo "- YOUTUBE_API_KEY"
        echo "- TWITTER_BEARER_TOKEN (and other Twitter API keys)"
        echo ""
        echo "After configuring your API keys, run this script again."
        exit 0
    else
        echo "❌ .env.docker.example not found"
        exit 1
    fi
fi

echo "✅ Environment file found"

# Create required directories
mkdir -p temp logs
echo "✅ Created required directories"

# Build and start core services
echo "🚀 Building and starting services..."
docker-compose up -d postgres soundhash_app

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker-compose exec -T postgres pg_isready -U soundhash_user -d soundhash > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "❌ PostgreSQL failed to start within 60 seconds"
    echo "Check logs with: docker-compose logs postgres"
    exit 1
fi

# Setup database schema
echo "🔧 Setting up database schema..."
docker-compose run --rm soundhash_setup

echo "✅ Database setup completed"

# Show status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 SoundHash is now running!"
echo ""
echo "Next steps:"
echo "1. Run channel ingestion: ./docker/manage.sh ingest"
echo "2. Start Twitter bot: ./docker/manage.sh bot"
echo "3. Check logs: ./docker/manage.sh logs"
echo "4. Stop services: ./docker/manage.sh stop"
echo ""
echo "PostgreSQL is available on port 5433"
echo "Access it with: psql -h localhost -p 5433 -U soundhash_user -d soundhash"