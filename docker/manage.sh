#!/bin/bash
# Docker management script for SoundHash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if docker and docker-compose are installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Setup environment file
setup_env() {
    log_info "Setting up environment file..."
    
    if [ ! -f .env.docker ]; then
        if [ -f .env.docker.example ]; then
            cp .env.docker.example .env.docker
            log_warning "Created .env.docker from example. Please edit it with your API keys."
        else
            log_error ".env.docker.example not found"
            exit 1
        fi
    else
        log_success "Environment file already exists"
    fi
}

# Create required directories
setup_directories() {
    log_info "Creating required directories..."
    
    mkdir -p temp logs
    chmod 755 temp logs
    
    log_success "Directories created"
}

# Build and start services
start_services() {
    log_info "Building and starting SoundHash services..."
    
    # Start core services (postgres + app)
    docker-compose up -d postgres soundhash_app
    
    log_info "Waiting for PostgreSQL to be ready..."
    
    # Wait for postgres to be healthy
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec postgres pg_isready -U soundhash_user -d soundhash &> /dev/null; then
            log_success "PostgreSQL is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "PostgreSQL failed to start within 60 seconds"
        exit 1
    fi
    
    log_success "Core services started successfully"
}

# Setup database schema
setup_database() {
    log_info "Setting up database schema..."
    
    docker-compose run --rm soundhash_setup
    
    log_success "Database setup completed"
}

# Run channel ingestion
run_ingestion() {
    log_info "Starting channel ingestion..."
    
    docker-compose run --rm soundhash_ingestion
    
    log_success "Channel ingestion completed"
}

# Start Twitter bot
start_bot() {
    log_info "Starting Twitter bot..."
    
    docker-compose up -d soundhash_twitter_bot
    
    log_success "Twitter bot started"
}

# Start authentication server
start_auth_server() {
    log_info "Starting authentication server..."
    
    docker-compose up -d soundhash_auth_server
    
    log_success "Authentication server started on http://localhost:8000"
    log_info "Available endpoints:"
    log_info "  - http://localhost:8000/auth/twitter (Twitter OAuth)"
    log_info "  - http://localhost:8000/auth/reddit (Reddit OAuth)"
    log_info "  - http://localhost:8000/auth/status (Check auth status)"
}

# Stop authentication server
stop_auth_server() {
    log_info "Stopping authentication server..."
    
    docker-compose stop soundhash_auth_server
    
    log_success "Authentication server stopped"
}

# Stop all services
stop_services() {
    log_info "Stopping all services..."
    
    docker-compose down
    
    log_success "All services stopped"
}

# Show service status
show_status() {
    log_info "Service status:"
    docker-compose ps
}

# Show logs
show_logs() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Cleanup containers and volumes
cleanup() {
    log_warning "This will remove all containers and volumes. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Cleaning up containers and volumes..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Main script logic
case "$1" in
    "start")
        check_dependencies
        setup_env
        setup_directories
        start_services
        setup_database
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 2
        start_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "ingest")
        run_ingestion
        ;;
    "bot")
        start_bot
        ;;
    "auth")
        start_auth_server
        ;;
    "auth-stop")
        stop_auth_server
        ;;
    "setup")
        check_dependencies
        setup_env
        setup_directories
        start_services
        setup_database
        log_success "Setup completed! You can now run './docker/manage.sh ingest' to start processing channels."
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"--help"|"-h"|"")
        echo "SoundHash Docker Management Script"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  setup     - Complete setup (start services, setup database)"
        echo "  start     - Start core services (postgres, app)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status"
        echo "  logs      - Show logs (optionally specify service name)"
        echo "  ingest    - Run channel ingestion"
        echo "  bot       - Start Twitter bot"
        echo "  auth      - Start authentication server"
        echo "  auth-stop - Stop authentication server"
        echo "  cleanup   - Remove all containers and volumes"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 setup          # Complete setup"
        echo "  $0 start          # Start services"
        echo "  $0 logs postgres  # Show postgres logs"
        echo "  $0 ingest         # Process YouTube channels"
        echo "  $0 auth           # Start OAuth server"
        echo ""
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' to see available commands."
        exit 1
        ;;
esac