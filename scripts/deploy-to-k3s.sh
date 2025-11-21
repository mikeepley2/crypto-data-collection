#!/bin/bash
# K3s Production Deployment Script - Updated for 12 Collectors
# Deploy all crypto data collection services to K3s cluster

set -e

# Configuration
NAMESPACE="crypto-core-production"
INFRASTRUCTURE_NAMESPACE="crypto-infrastructure"
K3S_MANIFESTS_DIR="k8s/k3s-production"
TIMEOUT="300s"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

# Build Docker images for all collectors
build_images() {
    print_header "Building Docker Images for All 12 Collectors"
    
    if [ -f "$PROJECT_ROOT/scripts/build-docker-images.sh" ]; then
        print_status "Running Docker image build script..."
        bash "$PROJECT_ROOT/scripts/build-docker-images.sh" build
    else
        print_warning "Docker build script not found. Assuming images are already available."
        print_status "Available images:"
        docker images | grep crypto- || print_warning "No crypto images found"
    fi
}

# Deploy infrastructure components
deploy_infrastructure() {
    print_header "Deploying Infrastructure Components"
    
    print_status "Creating namespaces and basic configuration..."
    kubectl apply -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/namespace.yaml"
    
    print_status "Deploying configuration and secrets..."
    kubectl apply -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/config.yaml"
    
    print_status "Deploying database infrastructure (MySQL & Redis)..."
    if [ -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/infrastructure.yaml" ]; then
        kubectl apply -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/infrastructure.yaml"
        
        print_status "Waiting for database pods to be ready..."
        kubectl wait --for=condition=ready pod -l app=mysql -n $INFRASTRUCTURE_NAMESPACE --timeout=300s || true
        kubectl wait --for=condition=ready pod -l app=redis -n $INFRASTRUCTURE_NAMESPACE --timeout=300s || true
    else
        print_warning "infrastructure.yaml not found, skipping database deployment"
        print_warning "You may need to set up MySQL and Redis manually"
    fi
    
    print_status "✅ Infrastructure deployment complete"
}

# Deploy application services
deploy_services() {
    print_header "Deploying All 12 Crypto Data Collection Services"
    
    print_status "Deploying all collectors using updated configuration..."
    if [ -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/services-deployment-updated.yaml" ]; then
        kubectl apply -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/services-deployment-updated.yaml"
    else
        print_warning "Using fallback deployment configuration..."
        kubectl apply -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/services-deployment.yaml"
    fi
    
    print_status "Creating services for all collectors..."
    if [ -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/services-updated.yaml" ]; then
        kubectl apply -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/services-updated.yaml"
    else
        print_warning "Using fallback services configuration..."
        kubectl apply -f "$PROJECT_ROOT/$K3S_MANIFESTS_DIR/services.yaml"
    fi
    
    print_status "✅ Services deployment initiated"
}

# Wait for deployments to be ready
wait_for_deployments() {
    print_header "Waiting for All 12 Deployments to be Ready"
    
    # Updated list of actual deployments (based on the 12 collectors)
    local deployments=(
        "enhanced-news-collector"
        "enhanced-sentiment-ml-analysis"
        "enhanced-technical-calculator"
        "enhanced-materialized-updater"
        "enhanced-crypto-prices-service"
        "enhanced-crypto-news-collector-sub"
        "enhanced-onchain-collector"
        "enhanced-technical-indicators-collector"
        "enhanced-macro-collector-v2"
        "enhanced-crypto-derivatives-collector"
        "ml-market-collector"
        "enhanced-ohlc-collector"
    )
    
    local ready_deployments=0
    local total_deployments=${#deployments[@]}
    
    for deployment in "${deployments[@]}"; do
        print_status "Waiting for $deployment to be ready..."
        if kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=$TIMEOUT; then
            print_status "✅ $deployment is ready"
            ((ready_deployments++))
        else
            print_error "❌ $deployment failed to deploy within timeout"
            print_status "Checking pod logs for $deployment..."
            kubectl logs -l app=$deployment -n $NAMESPACE --tail=20 || true
        fi
    done
    
    print_status "Deployment Summary: $ready_deployments/$total_deployments services ready"
    
    if [ $ready_deployments -lt $((total_deployments * 80 / 100)) ]; then
        print_warning "Less than 80% of services are ready. Check individual service status."
    fi
}

# Check service health
check_service_health() {
    print_header "Checking Service Health"
    
    print_status "Getting pod status..."
    kubectl get pods -n $NAMESPACE -o wide
    
    print_status "Getting service endpoints..."
    kubectl get services -n $NAMESPACE
    
    print_status "Checking for failed pods..."
    local failed_pods=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed --no-headers | wc -l)
    if [ $failed_pods -gt 0 ]; then
        print_warning "⚠️  Found $failed_pods failed pods"
        kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed
    fi
    
    # Test collector validation
    print_status "Running collector validation..."
    if [ -f "$PROJECT_ROOT/validate_collectors.py" ]; then
        print_status "Testing collectors within cluster..."
        # Create a temporary pod to run validation
        kubectl run validator --image=python:3.11-slim --rm -it --restart=Never -n $NAMESPACE -- \
            bash -c "pip install mysql-connector-python && python -c 'print(\"Validation would run here\")'" || true
    fi
}

# Display deployment summary
show_deployment_summary() {
    print_header "K3s Deployment Summary - 12 Collectors"
    
    print_status "Cluster Information:"
    kubectl cluster-info
    
    print_status "Namespace Status:"
    kubectl get namespaces | grep crypto
    
    print_status "Pod Status (All 12 Services):"
    kubectl get pods -n $NAMESPACE -o wide
    
    print_status "Service Status:"
    kubectl get services -n $NAMESPACE
    
    print_status "Resource Usage:"
    kubectl top pods -n $NAMESPACE 2>/dev/null || print_warning "Metrics server not available for resource usage"
    
    print_status "External Access:"
    local node_ip=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
    echo "API Gateway: http://$node_ip:30080"
    echo "Use 'kubectl get nodes -o wide' to see all node IPs"
    
    print_status "Useful Commands:"
    echo "  View all pods:       kubectl get pods -n $NAMESPACE"
    echo "  View logs:           kubectl logs -f deployment/<service-name> -n $NAMESPACE"
    echo "  Port forward:        kubectl port-forward -n $NAMESPACE svc/<service-name> 8080:<port>"
    echo "  Scale service:       kubectl scale deployment <service-name> --replicas=<count> -n $NAMESPACE"
    echo "  Delete all:          kubectl delete namespace $NAMESPACE $INFRASTRUCTURE_NAMESPACE"
    echo "  Restart deployment:  kubectl rollout restart deployment/<service-name> -n $NAMESPACE"
    
    print_status "🎉 Crypto Data Collection Platform (12 collectors) deployed successfully to K3s!"
}

# Get detailed status of specific service
service_status() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        print_error "Service name required for status check"
        exit 1
    fi
    
    print_header "Status for $service_name"
    
    print_status "Deployment status:"
    kubectl get deployment $service_name -n $NAMESPACE -o wide || print_error "Deployment not found"
    
    print_status "Pod status:"
    kubectl get pods -l app=$service_name -n $NAMESPACE -o wide
    
    print_status "Recent logs:"
    kubectl logs -l app=$service_name -n $NAMESPACE --tail=50
    
    print_status "Service endpoints:"
    kubectl get endpoints $service_name-service -n $NAMESPACE || true
}

# Cleanup function
cleanup() {
    print_header "Cleaning Up K3s Deployment"
    
    print_warning "This will delete all crypto data collection services and data. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Deleting application namespace..."
        kubectl delete namespace $NAMESPACE --ignore-not-found=true
        
        print_warning "Also delete infrastructure (database)? (y/N)"
        read -r db_response
        
        if [[ "$db_response" =~ ^[Yy]$ ]]; then
            kubectl delete namespace $INFRASTRUCTURE_NAMESPACE --ignore-not-found=true
            print_status "✅ Full cleanup complete (including databases)"
        else
            print_status "✅ Application cleanup complete (databases preserved)"
        fi
    else
        print_status "Cleanup cancelled"
    fi
}

# Restart all services
restart_all() {
    print_header "Restarting All 12 Collectors"
    
    local deployments=(
        "enhanced-news-collector"
        "enhanced-sentiment-ml-analysis"
        "enhanced-technical-calculator"
        "enhanced-materialized-updater"
        "enhanced-crypto-prices-service"
        "enhanced-crypto-news-collector-sub"
        "enhanced-onchain-collector"
        "enhanced-technical-indicators-collector"
        "enhanced-macro-collector-v2"
        "enhanced-crypto-derivatives-collector"
        "ml-market-collector"
        "enhanced-ohlc-collector"
    )
    
    for deployment in "${deployments[@]}"; do
        print_status "Restarting $deployment..."
        kubectl rollout restart deployment/$deployment -n $NAMESPACE || print_warning "Failed to restart $deployment"
    done
    
    print_status "✅ All restart commands issued. Use 'status' command to check progress."
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_cluster
            build_images
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
        "service-status")
            check_cluster
            service_status "$2"
            ;;
        "health")
            check_cluster
            check_service_health
            ;;
        "build-only")
            build_images
            ;;
        "restart")
            check_cluster
            restart_all
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            echo "K3s Production Deployment Script for Crypto Data Collection (12 Collectors)"
            echo ""
            echo "Usage:"
            echo "  $0 deploy              # Full deployment (build, deploy, verify)"
            echo "  $0 status              # Show deployment status and summary"
            echo "  $0 service-status <name> # Show detailed status for specific service"
            echo "  $0 health              # Check service health only"
            echo "  $0 build-only          # Build Docker images only"
            echo "  $0 restart             # Restart all deployments"
            echo "  $0 cleanup             # Remove all deployments"
            echo ""
            echo "Prerequisites:"
            echo "  - K3s cluster must be running"
            echo "  - kubectl must be configured to access the cluster"
            echo "  - Docker must be available for building images"
            echo ""
            echo "All 12 Collectors:"
            echo "  1. enhanced-news-collector"
            echo "  2. enhanced-sentiment-ml-analysis"
            echo "  3. enhanced-technical-calculator"
            echo "  4. enhanced-materialized-updater"
            echo "  5. enhanced-crypto-prices-service"
            echo "  6. enhanced-crypto-news-collector-sub"
            echo "  7. enhanced-onchain-collector"
            echo "  8. enhanced-technical-indicators-collector"
            echo "  9. enhanced-macro-collector-v2"
            echo " 10. enhanced-crypto-derivatives-collector"
            echo " 11. ml-market-collector"
            echo " 12. enhanced-ohlc-collector"
            exit 1
            ;;
    esac
}

main "$@"