#!/bin/bash

# Kubernetes Deployment Script
# Usage: ./deploy-k8s.sh [environment] [action]
# Environment: staging|production (default: staging)
# Action: deploy|rollback|status|logs (default: deploy)

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
K8S_DIR="${PROJECT_ROOT}/build/k8s"

# Default values
ENVIRONMENT="${1:-staging}"
ACTION="${2:-deploy}"
TIMEOUT="${TIMEOUT:-300s}"

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

# Check if kubectl is available
check_kubectl() {
    if ! command -v kubectl >/dev/null 2>&1; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
}

# Check if kustomize is available
check_kustomize() {
    if ! command -v kustomize >/dev/null 2>&1; then
        log_error "kustomize is not installed or not in PATH"
        exit 1
    fi
}

# Verify cluster connectivity
check_cluster() {
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    local cluster_info=$(kubectl cluster-info | grep "Kubernetes control plane" | head -1)
    log_info "Connected to: $cluster_info"
}

# Deploy using kustomize
deploy() {
    local env_dir="${K8S_DIR}/${ENVIRONMENT}"
    
    if [[ ! -d "$env_dir" ]]; then
        log_error "Environment directory not found: $env_dir"
        exit 1
    fi
    
    log_info "Deploying to $ENVIRONMENT environment..."
    
    # Build and apply manifests
    if kustomize build "$env_dir" | kubectl apply -f -; then
        log_success "Manifests applied successfully"
    else
        log_error "Failed to apply manifests"
        exit 1
    fi
    
    # Wait for deployments to be ready
    local namespace="crypto-${ENVIRONMENT}"
    log_info "Waiting for deployments to be ready (timeout: $TIMEOUT)..."
    
    for service in "${SERVICES[@]}"; do
        local deployment_name="${ENVIRONMENT}-${service}"
        log_info "Waiting for ${deployment_name}..."
        
        if kubectl rollout status deployment/"$deployment_name" \
            -n "$namespace" \
            --timeout="$TIMEOUT"; then
            log_success "$deployment_name is ready"
        else
            log_error "$deployment_name failed to become ready"
            return 1
        fi
    done
    
    log_success "All deployments are ready!"
}

# Rollback deployment
rollback() {
    local namespace="crypto-${ENVIRONMENT}"
    
    log_info "Rolling back deployments in $ENVIRONMENT..."
    
    for service in "${SERVICES[@]}"; do
        local deployment_name="${ENVIRONMENT}-${service}"
        log_info "Rolling back ${deployment_name}..."
        
        if kubectl rollout undo deployment/"$deployment_name" -n "$namespace"; then
            log_success "Rollback initiated for $deployment_name"
        else
            log_error "Failed to rollback $deployment_name"
        fi
    done
    
    # Wait for rollback to complete
    for service in "${SERVICES[@]}"; do
        local deployment_name="${ENVIRONMENT}-${service}"
        kubectl rollout status deployment/"$deployment_name" -n "$namespace" --timeout="$TIMEOUT"
    done
    
    log_success "Rollback completed!"
}

# Show deployment status
status() {
    local namespace="crypto-${ENVIRONMENT}"
    
    log_info "Deployment status for $ENVIRONMENT:"
    echo
    
    # Show pods
    echo "=== PODS ==="
    kubectl get pods -n "$namespace" -o wide
    echo
    
    # Show services
    echo "=== SERVICES ==="
    kubectl get services -n "$namespace"
    echo
    
    # Show deployments
    echo "=== DEPLOYMENTS ==="
    kubectl get deployments -n "$namespace"
    echo
    
    # Show HPA
    echo "=== HORIZONTAL POD AUTOSCALERS ==="
    kubectl get hpa -n "$namespace" 2>/dev/null || echo "No HPA found"
    echo
    
    # Show resource usage
    echo "=== RESOURCE USAGE ==="
    kubectl top pods -n "$namespace" 2>/dev/null || echo "Metrics server not available"
}

# Show logs
logs() {
    local namespace="crypto-${ENVIRONMENT}"
    local service="${3:-all}"
    local tail_lines="${4:-100}"
    
    if [[ "$service" == "all" ]]; then
        for svc in "${SERVICES[@]}"; do
            local deployment_name="${ENVIRONMENT}-${svc}"
            echo "=== LOGS FOR $deployment_name ==="
            kubectl logs -n "$namespace" \
                deployment/"$deployment_name" \
                --tail="$tail_lines" \
                --timestamps \
                --prefix=true || true
            echo
        done
    else
        local deployment_name="${ENVIRONMENT}-${service}"
        kubectl logs -n "$namespace" \
            deployment/"$deployment_name" \
            --tail="$tail_lines" \
            --timestamps \
            --follow
    fi
}

# Health check
health_check() {
    local namespace="crypto-${ENVIRONMENT}"
    
    log_info "Running health checks for $ENVIRONMENT..."
    
    for service in "${SERVICES[@]}"; do
        local deployment_name="${ENVIRONMENT}-${service}"
        local service_name="${deployment_name}-service"
        
        # Port forward and check health endpoint
        log_info "Checking health of $service..."
        
        # Get a pod for the service
        local pod=$(kubectl get pods -n "$namespace" \
            -l app="$service" \
            -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
        
        if [[ -n "$pod" ]]; then
            if kubectl exec -n "$namespace" "$pod" -- \
                curl -f -s http://localhost:8080/health >/dev/null 2>&1; then
                log_success "$service health check passed"
            else
                log_warning "$service health check failed"
            fi
        else
            log_warning "No pods found for $service"
        fi
    done
}

# Main execution
main() {
    case "$ACTION" in
        deploy)
            deploy
            health_check
            ;;
        rollback)
            rollback
            ;;
        status)
            status
            ;;
        logs)
            logs "$@"
            ;;
        health)
            health_check
            ;;
        *)
            log_error "Invalid action: $ACTION"
            usage
            ;;
    esac
}

# Script usage
usage() {
    echo "Usage: $0 [environment] [action] [options]"
    echo "  environment: staging|production (default: staging)"
    echo "  action: deploy|rollback|status|logs|health (default: deploy)"
    echo ""
    echo "Environment variables:"
    echo "  TIMEOUT: Deployment timeout (default: 300s)"
    echo ""
    echo "Examples:"
    echo "  $0 staging deploy           # Deploy to staging"
    echo "  $0 production deploy        # Deploy to production"
    echo "  $0 staging rollback         # Rollback staging deployment"
    echo "  $0 staging status           # Show deployment status"
    echo "  $0 staging logs             # Show logs for all services"
    echo "  $0 staging logs enhanced-news-collector  # Show logs for specific service"
    echo "  $0 staging health           # Run health checks"
    exit 1
}

# Check for help flag
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    usage
fi

# Check prerequisites
check_kubectl
check_kustomize
check_cluster

# Run main function
main "$@"