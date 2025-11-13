#!/bin/bash

# Development Environment Setup Script
# Sets up local development environment with Docker Compose

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DOCKER_DIR="${PROJECT_ROOT}/build/docker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    local missing_tools=()
    
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing_tools+=("docker-compose")
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and try again."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
}

# Setup development environment
setup_env() {
    log_info "Setting up development environment..."
    
    cd "$DOCKER_DIR"
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        log_info "Creating .env file..."
        cat > .env << EOF
# Database Configuration
POSTGRES_USER=crypto_user
POSTGRES_PASSWORD=crypto_dev_pass
POSTGRES_DB=crypto_data

# Redis Configuration
REDIS_PASSWORD=

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# External APIs (add your keys here)
RSS_API_KEY=
SENTIMENT_API_KEY=

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin123
EOF
        log_success "Created .env file"
    fi
    
    # Pull required images
    log_info "Pulling required Docker images..."
    docker-compose pull postgres redis prometheus grafana
    
    # Start infrastructure services first
    log_info "Starting infrastructure services..."
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    until docker-compose exec postgres pg_isready -U crypto_user >/dev/null 2>&1; do
        sleep 2
    done
    log_success "Database is ready"
    
    # Setup database schema
    setup_database
    
    # Build and start application services
    log_info "Building and starting application services..."
    docker-compose up -d --build
    
    # Wait for services to be healthy
    wait_for_services
    
    log_success "Development environment is ready!"
    show_service_info
}

# Setup database schema
setup_database() {
    log_info "Setting up database schema..."
    
    # Create init script
    cat > init-db.sql << 'EOF'
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS crypto_data;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Sample tables (you can add your actual schema here)
CREATE TABLE IF NOT EXISTS crypto_data.news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crypto_data.sentiment_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES crypto_data.news_articles(id),
    sentiment_score DECIMAL(5,4),
    confidence DECIMAL(5,4),
    model_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON crypto_data.news_articles(published_at);
CREATE INDEX IF NOT EXISTS idx_sentiment_scores_article_id ON crypto_data.sentiment_scores(article_id);

GRANT ALL PRIVILEGES ON SCHEMA crypto_data TO crypto_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA crypto_data TO crypto_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA crypto_data TO crypto_user;
EOF
    
    docker-compose exec postgres psql -U crypto_user -d crypto_data -f /docker-entrypoint-initdb.d/init-db.sql
    log_success "Database schema setup complete"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local services=("enhanced-news-collector" "enhanced-sentiment-ml" "enhanced-technical-calculator" "enhanced-materialized-updater")
    local ports=(8080 8081 8082 8083)
    
    for i in "${!services[@]}"; do
        local service="${services[$i]}"
        local port="${ports[$i]}"
        
        log_info "Waiting for $service on port $port..."
        
        local attempts=0
        local max_attempts=30
        
        while [[ $attempts -lt $max_attempts ]]; do
            if curl -f -s "http://localhost:$port/health" >/dev/null 2>&1; then
                log_success "$service is healthy"
                break
            fi
            
            ((attempts++))
            sleep 2
        done
        
        if [[ $attempts -eq $max_attempts ]]; then
            log_warning "$service may not be healthy yet"
        fi
    done
}

# Show service information
show_service_info() {
    echo
    log_info "Development environment is running!"
    echo
    echo "Services:"
    echo "  Enhanced News Collector:      http://localhost:8080"
    echo "  Enhanced Sentiment ML:        http://localhost:8081"
    echo "  Enhanced Technical Calculator: http://localhost:8082"
    echo "  Enhanced Materialized Updater: http://localhost:8083"
    echo
    echo "Infrastructure:"
    echo "  PostgreSQL:    localhost:5432"
    echo "  Redis:         localhost:6379"
    echo "  Prometheus:    http://localhost:9090"
    echo "  Grafana:       http://localhost:3000 (admin/admin123)"
    echo
    echo "Useful commands:"
    echo "  View logs:     docker-compose logs -f [service_name]"
    echo "  Stop all:      docker-compose down"
    echo "  Restart:       docker-compose restart [service_name]"
    echo "  Database CLI:  docker-compose exec postgres psql -U crypto_user -d crypto_data"
    echo "  Redis CLI:     docker-compose exec redis redis-cli"
}

# Stop development environment
stop_env() {
    log_info "Stopping development environment..."
    cd "$DOCKER_DIR"
    docker-compose down
    log_success "Development environment stopped"
}

# Clean development environment
clean_env() {
    log_info "Cleaning development environment..."
    cd "$DOCKER_DIR"
    docker-compose down -v --remove-orphans
    docker-compose rm -f
    
    # Remove built images
    local services=("enhanced-news-collector" "enhanced-sentiment-ml" "enhanced-technical-calculator" "enhanced-materialized-updater")
    for service in "${services[@]}"; do
        docker rmi "crypto/${service}:latest" 2>/dev/null || true
    done
    
    log_success "Development environment cleaned"
}

# Show logs
show_logs() {
    cd "$DOCKER_DIR"
    if [[ ${#@} -gt 0 ]]; then
        docker-compose logs -f "$@"
    else
        docker-compose logs -f
    fi
}

# Main function
main() {
    local action="${1:-start}"
    
    case "$action" in
        start|setup)
            check_prerequisites
            setup_env
            ;;
        stop)
            stop_env
            ;;
        clean)
            clean_env
            ;;
        restart)
            stop_env
            check_prerequisites
            setup_env
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        status)
            cd "$DOCKER_DIR"
            docker-compose ps
            ;;
        *)
            echo "Usage: $0 {start|stop|clean|restart|logs|status}"
            echo ""
            echo "Commands:"
            echo "  start    - Start development environment"
            echo "  stop     - Stop all services"
            echo "  clean    - Stop and remove all containers, volumes, and images"
            echo "  restart  - Stop and start again"
            echo "  logs     - Show logs (optionally specify service name)"
            echo "  status   - Show container status"
            exit 1
            ;;
    esac
}

main "$@"