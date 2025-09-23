#!/bin/bash

# Data Collection Node Deployment Script
# Deploy the dedicated data collection infrastructure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DATA_COLLECTION_DIR="$PROJECT_ROOT/k8s"

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
}

# Deploy function
deploy() {
    log "Deploying dedicated data collection node..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is required but not installed"
        exit 1
    fi
    
    # Deploy in order
    log "Creating namespace and basic configuration..."
    kubectl apply -f "$K8S_DATA_COLLECTION_DIR/00-namespace.yaml"
    kubectl apply -f "$K8S_DATA_COLLECTION_DIR/01-configmaps.yaml"
    
    # Note: Secrets need to be configured manually with real API keys
    warning "Please update the secrets in 02-secrets.yaml with your actual API keys before deploying"
    warning "The current secrets file contains placeholder values"
    
    # Deploy databases
    log "Deploying dedicated databases..."
    kubectl apply -f "$K8S_DATA_COLLECTION_DIR/databases/"
    
    # Wait for databases
    log "Waiting for databases to be ready..."
    kubectl wait --for=condition=available deployment/mysql-data-collection -n crypto-data-collection --timeout=300s
    kubectl wait --for=condition=available deployment/redis-data-collection -n crypto-data-collection --timeout=300s
    
    # Deploy API Gateway
    log "Deploying Data API Gateway..."
    kubectl apply -f "$K8S_DATA_COLLECTION_DIR/api/"
    
    # Wait for API Gateway
    kubectl wait --for=condition=available deployment/data-api-gateway -n crypto-data-collection --timeout=300s
    
    success "Data collection node deployed successfully!"
    
    # Show status
    log "Data collection node status:"
    kubectl get pods -n crypto-data-collection
    
    echo
    echo "================================================================="
    echo "🎉 DATA COLLECTION NODE DEPLOYED 🎉"
    echo "================================================================="
    echo
    echo "✅ Namespace: crypto-data-collection"
    echo "✅ Databases: MySQL, Redis deployed"
    echo "✅ API Gateway: Available on port 8000"
    echo
    echo "📋 Next Steps:"
    echo "1. Update secrets with real API keys:"
    echo "   kubectl edit secret api-keys -n crypto-data-collection"
    echo "   kubectl edit secret database-credentials -n crypto-data-collection"
    echo
    echo "2. Deploy collection services (customize as needed):"
    echo "   kubectl apply -f k8s/data-collection-node/collectors/"
    echo
    echo "3. Test API access:"
    echo "   kubectl port-forward svc/data-api-gateway 8000:8000 -n crypto-data-collection"
    echo "   curl http://localhost:8000/health"
    echo
    echo "4. Configure trading system to use data APIs"
    echo "================================================================="
}

# Main execution
main() {
    case "${1:-deploy}" in
        "deploy")
            deploy
            ;;
        "status")
            kubectl get all -n crypto-data-collection
            ;;
        "logs")
            kubectl logs -f deployment/data-api-gateway -n crypto-data-collection
            ;;
        "delete")
            read -p "Are you sure you want to delete the data collection node? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kubectl delete namespace crypto-data-collection
                success "Data collection node deleted"
            fi
            ;;
        *)
            echo "Usage: $0 [deploy|status|logs|delete]"
            echo "  deploy  - Deploy the data collection node (default)"
            echo "  status  - Show status of all resources"
            echo "  logs    - Follow API gateway logs"
            echo "  delete  - Delete the entire data collection node"
            ;;
    esac
}

main "$@"