#!/bin/bash
set -e

# Enhanced Onchain Data Collector Deployment Script
# This script builds the Docker image and deploys to Kubernetes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="onchain-collector"
IMAGE_NAME="crypto-data-collection/${SERVICE_NAME}"
NAMESPACE="crypto-data-collection"
BUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Parse command line arguments
ENVIRONMENT="staging"
BUILD_ONLY=false
SKIP_TESTS=false
FORCE_REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Deployment environment (staging|production) [default: staging]"
            echo "  --build-only            Only build Docker image, don't deploy"
            echo "  --skip-tests           Skip running tests before deployment"
            echo "  --force-rebuild        Force rebuild of Docker image"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    error "Environment must be 'staging' or 'production'"
fi

log "🚀 Starting deployment for ${SERVICE_NAME} to ${ENVIRONMENT}"

# Step 1: Pre-deployment checks
log "📋 Running pre-deployment checks..."

# Check if required files exist
REQUIRED_FILES=(
    "${PROJECT_ROOT}/services/onchain-collection/enhanced_onchain_collector.py"
    "${BUILD_DIR}/docker/onchain-collector.Dockerfile"
    "${BUILD_DIR}/k8s/base/onchain-collector.yaml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        error "Required file not found: $file"
    fi
done

success "All required files found"

# Step 2: Run tests (unless skipped)
if [[ "$SKIP_TESTS" != true ]]; then
    log "🧪 Running tests..."
    
    cd "$PROJECT_ROOT"
    
    # Run our verification script
    if python tests/verify_onchain_collector.py; then
        success "All tests passed"
    else
        error "Tests failed. Use --skip-tests to deploy anyway (not recommended)"
    fi
else
    warning "Skipping tests as requested"
fi

# Step 3: Build Docker image
log "🐳 Building Docker image..."

cd "$PROJECT_ROOT"

# Check if image exists and if we should rebuild
IMAGE_TAG="${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)"
LATEST_TAG="${IMAGE_NAME}:latest"

if [[ "$FORCE_REBUILD" == true ]] || ! docker image inspect "$LATEST_TAG" >/dev/null 2>&1; then
    log "Building new Docker image: $IMAGE_TAG"
    
    # Build the image
    docker build \
        -f "build/docker/onchain-collector.Dockerfile" \
        -t "$IMAGE_TAG" \
        -t "$LATEST_TAG" \
        --target production \
        .
    
    success "Docker image built: $IMAGE_TAG"
else
    log "Using existing Docker image: $LATEST_TAG"
    IMAGE_TAG="$LATEST_TAG"
fi

# Step 4: Test Docker image
log "🔍 Testing Docker image..."

# Run a quick test of the Docker image
CONTAINER_ID=$(docker run -d --name "${SERVICE_NAME}-test" "$IMAGE_TAG" sleep 30)

# Wait a moment for container to start
sleep 5

# Check if container is running
if docker ps | grep -q "${SERVICE_NAME}-test"; then
    success "Docker image test passed"
else
    error "Docker image test failed"
fi

# Cleanup test container
docker stop "$CONTAINER_ID" >/dev/null 2>&1
docker rm "$CONTAINER_ID" >/dev/null 2>&1

if [[ "$BUILD_ONLY" == true ]]; then
    success "Build completed. Image: $IMAGE_TAG"
    exit 0
fi

# Step 5: Deploy to Kubernetes
log "☸️  Deploying to Kubernetes ($ENVIRONMENT)..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    error "kubectl is not installed or not in PATH"
fi

# Check cluster connection
if ! kubectl cluster-info >/dev/null 2>&1; then
    error "Cannot connect to Kubernetes cluster"
fi

# Create namespace if it doesn't exist
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Apply base configuration
log "Applying base Kubernetes manifests..."
kubectl apply -f "${BUILD_DIR}/k8s/base/"

# Apply environment-specific configuration
if [[ -d "${BUILD_DIR}/k8s/${ENVIRONMENT}" ]]; then
    log "Applying ${ENVIRONMENT} specific configuration..."
    kubectl apply -k "${BUILD_DIR}/k8s/${ENVIRONMENT}/"
else
    warning "No environment-specific configuration found for ${ENVIRONMENT}"
fi

# Update deployment with new image
kubectl set image deployment/${SERVICE_NAME} \
    ${SERVICE_NAME}="$IMAGE_TAG" \
    -n "$NAMESPACE"

# Wait for rollout to complete
log "⏳ Waiting for deployment rollout..."
if kubectl rollout status deployment/${SERVICE_NAME} -n "$NAMESPACE" --timeout=300s; then
    success "Deployment rollout completed"
else
    error "Deployment rollout failed or timed out"
fi

# Step 6: Verify deployment
log "✅ Verifying deployment..."

# Check pod status
PODS=$(kubectl get pods -n "$NAMESPACE" -l app="${SERVICE_NAME}" --no-headers)
if [[ -z "$PODS" ]]; then
    error "No pods found for ${SERVICE_NAME}"
fi

echo "Pod status:"
kubectl get pods -n "$NAMESPACE" -l app="${SERVICE_NAME}"

# Check service
SERVICE_STATUS=$(kubectl get service "${SERVICE_NAME}-service" -n "$NAMESPACE" --no-headers 2>/dev/null || echo "")
if [[ -n "$SERVICE_STATUS" ]]; then
    success "Service is running"
    kubectl get service "${SERVICE_NAME}-service" -n "$NAMESPACE"
else
    warning "Service not found or not ready"
fi

# Step 7: Health check
log "🏥 Running health check..."

# Get a pod name
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app="${SERVICE_NAME}" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [[ -n "$POD_NAME" ]]; then
    # Wait a bit for the application to start
    sleep 10
    
    # Check health endpoint
    if kubectl exec -n "$NAMESPACE" "$POD_NAME" -- curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "Health check passed"
    else
        warning "Health check failed - application may still be starting"
    fi
else
    warning "No pods available for health check"
fi

# Step 8: Deployment summary
log "📊 Deployment Summary"
echo "===================="
echo "Service: ${SERVICE_NAME}"
echo "Environment: ${ENVIRONMENT}"
echo "Namespace: ${NAMESPACE}"
echo "Image: ${IMAGE_TAG}"
echo "Timestamp: $(date)"

# Final status
kubectl get all -n "$NAMESPACE" -l app="${SERVICE_NAME}"

success "🎉 Deployment completed successfully!"

log "💡 Useful commands:"
echo "  View logs: kubectl logs -f deployment/${SERVICE_NAME} -n ${NAMESPACE}"
echo "  Check status: kubectl get all -n ${NAMESPACE} -l app=${SERVICE_NAME}"
echo "  Scale deployment: kubectl scale deployment/${SERVICE_NAME} --replicas=2 -n ${NAMESPACE}"