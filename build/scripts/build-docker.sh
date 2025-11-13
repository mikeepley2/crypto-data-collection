#!/bin/bash

# Build and Push Docker Images Script
# Usage: ./build-docker.sh [environment] [push]
# Environment: development|staging|production (default: development)
# Push: true|false (default: false)

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DOCKER_DIR="${PROJECT_ROOT}/build/docker"

# Default values
ENVIRONMENT="${1:-development}"
PUSH="${2:-false}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Service definitions
SERVICES=(
    "enhanced-news-collector"
    "enhanced-sentiment-ml"
    "enhanced-technical-calculator"
    "enhanced-materialized-updater"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Build single service
build_service() {
    local service=$1
    local dockerfile="${DOCKER_DIR}/Dockerfile.${service}"
    local image_name="${DOCKER_REGISTRY:+${DOCKER_REGISTRY}/}crypto-${service}"
    local full_tag="${image_name}:${IMAGE_TAG}"
    
    if [[ ! -f "$dockerfile" ]]; then
        log_error "Dockerfile not found: $dockerfile"
        return 1
    fi
    
    log_info "Building $service..."
    
    # Build with appropriate target
    local target="production"
    if [[ "$ENVIRONMENT" == "development" ]]; then
        target="development"
    fi
    
    if docker build \
        --file "$dockerfile" \
        --target "$target" \
        --tag "$full_tag" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        --build-arg BUILD_DATE="$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        --build-arg VCS_REF="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')" \
        "$PROJECT_ROOT"; then
        log_success "Built $service successfully"
        
        # Tag with environment-specific tag
        local env_tag="${image_name}:${ENVIRONMENT}-${IMAGE_TAG}"
        docker tag "$full_tag" "$env_tag"
        log_info "Tagged as $env_tag"
        
        return 0
    else
        log_error "Failed to build $service"
        return 1
    fi
}

# Push single service
push_service() {
    local service=$1
    local image_name="${DOCKER_REGISTRY:+${DOCKER_REGISTRY}/}crypto-${service}"
    local full_tag="${image_name}:${IMAGE_TAG}"
    local env_tag="${image_name}:${ENVIRONMENT}-${IMAGE_TAG}"
    
    if [[ "$PUSH" == "true" ]]; then
        log_info "Pushing $service..."
        
        if docker push "$full_tag" && docker push "$env_tag"; then
            log_success "Pushed $service successfully"
        else
            log_error "Failed to push $service"
            return 1
        fi
    fi
}

# Main execution
main() {
    log_info "Starting Docker build process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Push: $PUSH"
    log_info "Image Tag: $IMAGE_TAG"
    
    # Check prerequisites
    check_docker
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Build services
    failed_services=()
    
    for service in "${SERVICES[@]}"; do
        if build_service "$service"; then
            push_service "$service" || failed_services+=("$service")
        else
            failed_services+=("$service")
        fi
    done
    
    # Summary
    echo
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_success "All services built successfully!"
    else
        log_error "Failed to build/push services: ${failed_services[*]}"
        exit 1
    fi
    
    # Display built images
    echo
    log_info "Built images:"
    for service in "${SERVICES[@]}"; do
        local image_name="${DOCKER_REGISTRY:+${DOCKER_REGISTRY}/}crypto-${service}"
        echo "  - ${image_name}:${IMAGE_TAG}"
        echo "  - ${image_name}:${ENVIRONMENT}-${IMAGE_TAG}"
    done
}

# Script usage
usage() {
    echo "Usage: $0 [environment] [push]"
    echo "  environment: development|staging|production (default: development)"
    echo "  push: true|false (default: false)"
    echo ""
    echo "Environment variables:"
    echo "  DOCKER_REGISTRY: Docker registry URL (optional)"
    echo "  IMAGE_TAG: Image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0                          # Build for development"
    echo "  $0 production true          # Build and push for production"
    echo "  DOCKER_REGISTRY=my-registry.com IMAGE_TAG=v1.0.0 $0 staging true"
    exit 1
}

# Check for help flag
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    usage
fi

# Run main function
main "$@"