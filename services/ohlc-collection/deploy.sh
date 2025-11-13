#!/bin/bash
# Enhanced OHLC Collector - Kubernetes Build & Deploy Script

set -e

SERVICE_NAME="enhanced-ohlc-collector"
NAMESPACE="crypto-data-collection"
IMAGE_TAG="latest"
BUILD_CONTEXT="./services/ohlc-collection"

echo "🚀 Building and Deploying Enhanced OHLC Collector to Kubernetes"
echo "=============================================================="

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo "❌ kubectl is not installed or not in PATH"
        echo "Please install kubectl and ensure it's configured for your cluster"
        exit 1
    fi
    echo "✅ kubectl found"
}

# Function to check if docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed or not in PATH"
        echo "Please install Docker"
        exit 1
    fi
    echo "✅ Docker found"
}

# Function to create namespace if it doesn't exist
create_namespace() {
    echo "📝 Creating namespace if it doesn't exist..."
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    echo "✅ Namespace $NAMESPACE ready"
}

# Function to build Docker image
build_image() {
    echo "🔨 Building Docker image..."
    # Build from current directory since we're already in the service directory
    docker build -t crypto-data-collection/$SERVICE_NAME:$IMAGE_TAG .
    echo "✅ Docker image built: crypto-data-collection/$SERVICE_NAME:$IMAGE_TAG"
}

# Function to deploy to Kubernetes
deploy_to_k8s() {
    echo "🚢 Deploying to Kubernetes..."
    
    # Apply ConfigMap and deployment from current directory
    kubectl apply -f ohlc-deployment.yaml -n $NAMESPACE
    
    echo "✅ Deployment applied to namespace $NAMESPACE"
}

# Function to wait for deployment to be ready
wait_for_deployment() {
    echo "⏳ Waiting for deployment to be ready..."
    kubectl rollout status deployment/$SERVICE_NAME -n $NAMESPACE --timeout=300s
    echo "✅ Deployment is ready"
}

# Function to show deployment status
show_status() {
    echo ""
    echo "📊 Deployment Status:"
    echo "===================="
    kubectl get pods -l app=$SERVICE_NAME -n $NAMESPACE
    echo ""
    kubectl get services -l app=$SERVICE_NAME -n $NAMESPACE
    echo ""
    
    # Get pod name for logs
    POD_NAME=$(kubectl get pods -l app=$SERVICE_NAME -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$POD_NAME" ]; then
        echo "📋 Recent logs from $POD_NAME:"
        echo "================================"
        kubectl logs $POD_NAME -n $NAMESPACE --tail=20
        echo ""
        echo "🔗 To follow logs: kubectl logs -f $POD_NAME -n $NAMESPACE"
        echo "🔍 To test health: kubectl port-forward -n $NAMESPACE service/$SERVICE_NAME-service 8002:8002"
    fi
}

# Function to test the deployment
test_deployment() {
    echo "🧪 Testing deployment..."
    
    # Port forward in background for testing
    kubectl port-forward -n $NAMESPACE service/${SERVICE_NAME}-service 8002:8002 &
    PORT_FORWARD_PID=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Test health endpoint
    if curl -s http://localhost:8002/health > /dev/null; then
        echo "✅ Health check passed"
        
        # Test status endpoint
        echo "📊 Service Status:"
        curl -s http://localhost:8002/status | jq . || curl -s http://localhost:8002/status
        
    else
        echo "❌ Health check failed"
    fi
    
    # Clean up port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
}

# Main execution
main() {
    echo "Starting deployment process..."
    
    check_kubectl
    check_docker
    create_namespace
    build_image
    deploy_to_k8s
    wait_for_deployment
    show_status
    
    echo ""
    echo "🎉 Deployment complete!"
    echo ""
    echo "Next steps:"
    echo "- Test the service: kubectl port-forward -n $NAMESPACE service/${SERVICE_NAME}-service 8002:8002"
    echo "- Check logs: kubectl logs -f deployment/$SERVICE_NAME -n $NAMESPACE"
    echo "- Monitor health: curl http://localhost:8002/health"
    echo "- Trigger collection: curl -X POST http://localhost:8002/collect"
}

# Handle script arguments
case "${1:-deploy}" in
    "build")
        check_docker
        build_image
        ;;
    "deploy")
        main
        ;;
    "test")
        test_deployment
        ;;
    "status")
        show_status
        ;;
    "logs")
        POD_NAME=$(kubectl get pods -l app=$SERVICE_NAME -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}')
        kubectl logs -f $POD_NAME -n $NAMESPACE
        ;;
    *)
        echo "Usage: $0 [build|deploy|test|status|logs]"
        echo ""
        echo "Commands:"
        echo "  build  - Build Docker image only"
        echo "  deploy - Full build and deploy (default)"
        echo "  test   - Test the deployed service"
        echo "  status - Show deployment status"
        echo "  logs   - Follow pod logs"
        exit 1
        ;;
esac