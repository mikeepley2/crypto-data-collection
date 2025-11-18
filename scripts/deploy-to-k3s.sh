#!/bin/bash
# K3s Production Deployment Script
# Deploy all crypto data collection services to K3s cluster

set -e

# Configuration
NAMESPACE="crypto-core-production"
INFRASTRUCTURE_NAMESPACE="crypto-infrastructure"
K3S_MANIFESTS_DIR="k8s/k3s-production"
TIMEOUT="300s"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if kubectl is available and cluster is accessible
check_cluster() {
    print_status "Checking K3s cluster connectivity..."
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to K3s cluster. Make sure K3s is running and kubectl is configured."
        exit 1
    fi
    
    print_status "✅ Connected to K3s cluster"
    kubectl get nodes
}

# Deploy infrastructure components
deploy_infrastructure() {
    print_header "Deploying Infrastructure Components"
    
    print_status "Creating namespaces..."
    kubectl apply -f $K3S_MANIFESTS_DIR/namespace.yaml
    
    print_status "Deploying configuration and secrets..."
    kubectl apply -f $K3S_MANIFESTS_DIR/config.yaml
    
    print_status "Deploying database infrastructure..."
    if [ -f "$K3S_MANIFESTS_DIR/infrastructure.yaml" ]; then
        kubectl apply -f $K3S_MANIFESTS_DIR/infrastructure.yaml
    else
        print_warning "infrastructure.yaml not found, skipping database deployment"
        print_warning "You may need to set up MySQL and Redis manually"
    fi
    
    print_status "✅ Infrastructure deployment complete"
}

# Deploy application services
deploy_services() {
    print_header "Deploying Crypto Data Collection Services"
    
    print_status "Deploying all 10 microservices..."
    kubectl apply -f $K3S_MANIFESTS_DIR/services-deployment.yaml
    
    print_status "Creating services..."
    kubectl apply -f $K3S_MANIFESTS_DIR/services.yaml
    
    print_status "✅ Services deployment initiated"
}

# Wait for deployments to be ready
wait_for_deployments() {
    print_header "Waiting for Deployments to be Ready"
    
    local deployments=(
        "news-collector"
        "sentiment-analyzer"
        "technical-analysis-collector"
        "macro-economic-collector"
        "onchain-data-collector"
        "social-sentiment-collector"
        "enhanced-ohlc-collector"
        "price-collector"
        "ml-pipeline"
        "portfolio-optimization"
    )
    
    for deployment in "${deployments[@]}"; do
        print_status "Waiting for $deployment to be ready..."
        if kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=$TIMEOUT; then
            print_status "✅ $deployment is ready"
        else
            print_error "❌ $deployment failed to deploy within timeout"
        fi
    done
}

# Check service health
check_service_health() {
    print_header "Checking Service Health"
    
    print_status "Getting pod status..."
    kubectl get pods -n $NAMESPACE
    
    print_status "Getting service endpoints..."
    kubectl get services -n $NAMESPACE
    
    print_status "Checking service health endpoints..."
    local services=(
        "news-collector-service:8001"
        "sentiment-analyzer-service:8002"
        "technical-analysis-collector-service:8003"
        "macro-economic-collector-service:8004"
        "onchain-data-collector-service:8005"
        "social-sentiment-collector-service:8006"
        "enhanced-ohlc-collector-service:8007"
        "price-collector-service:8008"
        "ml-pipeline-service:8009"
        "portfolio-optimization-service:8010"
    )
    
    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d: -f1)
        service_port=$(echo $service | cut -d: -f2)
        
        print_status "Testing $service_name health endpoint..."
        
        # Use kubectl port-forward to test health endpoint
        kubectl port-forward -n $NAMESPACE svc/$service_name $service_port:$service_port &
        local pf_pid=$!
        sleep 3
        
        if curl -sf http://localhost:$service_port/health &>/dev/null; then
            print_status "✅ $service_name health check passed"
        else
            print_warning "⚠️  $service_name health check failed (service may still be starting)"
        fi
        
        kill $pf_pid 2>/dev/null || true
        sleep 1
    done
}

# Display deployment summary
show_deployment_summary() {
    print_header "Deployment Summary"
    
    print_status "Cluster Information:"
    kubectl cluster-info
    
    print_status "Namespace Status:"
    kubectl get namespaces | grep crypto
    
    print_status "Pod Status:"
    kubectl get pods -n $NAMESPACE -o wide
    
    print_status "Service Status:"
    kubectl get services -n $NAMESPACE
    
    print_status "External Access:"
    echo "API Gateway: http://<node-ip>:30080"
    echo "Use 'kubectl get nodes -o wide' to see node IPs"
    
    print_status "Useful Commands:"
    echo "  View logs:        kubectl logs -f deployment/<service-name> -n $NAMESPACE"
    echo "  Port forward:     kubectl port-forward -n $NAMESPACE svc/<service-name> 8080:<port>"
    echo "  Scale service:    kubectl scale deployment <service-name> --replicas=<count> -n $NAMESPACE"
    echo "  Delete all:       kubectl delete namespace $NAMESPACE"
    
    print_status "🎉 Crypto Data Collection Platform deployed successfully to K3s!"
}

# Cleanup function
cleanup() {
    print_header "Cleaning Up Deployment"
    
    print_warning "This will delete all crypto data collection services. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        kubectl delete namespace $NAMESPACE --ignore-not-found=true
        kubectl delete namespace $INFRASTRUCTURE_NAMESPACE --ignore-not-found=true
        print_status "✅ Cleanup complete"
    else
        print_status "Cleanup cancelled"
    fi
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_cluster
            deploy_infrastructure
            deploy_services
            wait_for_deployments
            check_service_health
            show_deployment_summary
            ;;
        "status")
            check_cluster
            show_deployment_summary
            ;;
        "cleanup")
            cleanup
            ;;
        "health")
            check_cluster
            check_service_health
            ;;
        *)
            echo "K3s Production Deployment Script for Crypto Data Collection"
            echo ""
            echo "Usage:"
            echo "  $0 deploy     # Deploy all services to K3s"
            echo "  $0 status     # Show deployment status"
            echo "  $0 health     # Check service health"
            echo "  $0 cleanup    # Remove all deployments"
            echo ""
            echo "Prerequisites:"
            echo "  - K3s cluster must be running"
            echo "  - kubectl must be configured to access the cluster"
            echo "  - Docker images must be available in registry"
            exit 1
            ;;
    esac
}

main "$@"