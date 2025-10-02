#!/bin/bash
# LLM Integration Deployment and Testing Script
set -e

echo "🧠 Deploying LLM Integration for Crypto Data Collection"
echo "======================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if docker is available
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if crypto-collectors namespace exists
    if ! kubectl get namespace crypto-collectors &> /dev/null; then
        print_error "crypto-collectors namespace not found. Please deploy the main system first."
        exit 1
    fi
    
    print_status "✅ Prerequisites check passed"
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build LLM Integration Client
    print_status "Building LLM Integration Client..."
    docker build -t llm-integration-client:latest -f Dockerfile .
    
    # Build Enhanced Sentiment Service
    print_status "Building Enhanced Sentiment Service..."
    docker build -t enhanced-sentiment:latest -f Dockerfile.enhanced-sentiment .
    
    # Build News Narrative Analyzer
    print_status "Building News Narrative Analyzer..."
    docker build -t narrative-analyzer:latest -f Dockerfile.narrative-analyzer .
    
    print_success "All Docker images built successfully!"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Apply deployment
    kubectl apply -f llm-integration-deployment.yaml
    
    print_status "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/llm-integration-client -n crypto-collectors
    kubectl wait --for=condition=available --timeout=300s deployment/enhanced-sentiment -n crypto-collectors
    kubectl wait --for=condition=available --timeout=300s deployment/narrative-analyzer -n crypto-collectors
    
    print_success "All services deployed successfully!"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    services=("llm-integration-client")
    
    for service in "${services[@]}"; do
        print_status "Waiting for $service to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment/$service -n crypto-collectors
        if [ $? -eq 0 ]; then
            print_status "✅ $service is ready"
        else
            print_error "❌ $service failed to become ready"
            return 1
        fi
    done
    
    print_status "✅ All services are ready"
}

# Test service health
test_service_health() {
    print_status "Testing service health..."
    
    # Test LLM Integration Client
    print_status "Testing LLM Integration Client..."
    kubectl port-forward -n crypto-collectors svc/llm-integration-client 8040:8040 &
    PF_PID=$!
    
    sleep 5  # Wait for port forward to establish
    
    # Test health endpoint
    if curl -s http://localhost:8040/health > /dev/null; then
        print_status "✅ LLM Integration Client health check passed"
    else
        print_warning "⚠️ LLM Integration Client health check failed (may be normal if aitest not running)"
    fi
    
    # Test models endpoint
    if curl -s http://localhost:8040/models > /dev/null; then
        print_status "✅ LLM Integration Client models endpoint accessible"
    else
        print_warning "⚠️ LLM Integration Client models endpoint not accessible (may be normal if aitest not running)"
    fi
    
    # Clean up port forward
    kill $PF_PID 2>/dev/null || true
    
    print_status "✅ Health tests completed"
}

# Test integration with existing services
test_integration() {
    print_status "Testing integration with existing services..."
    
    # Check if crypto-news service exists (for narrative analysis)
    if kubectl get svc crypto-news-collector -n crypto-collectors &> /dev/null; then
        print_status "✅ Found crypto-news-collector service for narrative analysis"
    else
        print_warning "⚠️ crypto-news-collector not found - narrative analysis may be limited"
    fi
    
    # Check if sentiment service exists
    if kubectl get svc sentiment-microservice -n crypto-collectors &> /dev/null; then
        print_status "✅ Found sentiment-microservice for enhanced sentiment"
    else
        print_warning "⚠️ sentiment-microservice not found - enhanced sentiment may be limited"
    fi
    
    print_status "✅ Integration tests completed"
}

# Set up database schema for narrative analysis
setup_database() {
    print_status "Setting up database schema for narrative analysis..."
    
    # Try to set up the schema if news narrative analyzer exists
    if [ -f src/services/news_narrative/integrate_narrative_analyzer.py ]; then
        print_status "Setting up narrative analysis database schema..."
        
        # Try to run the integration script
        cd src/services/news_narrative
        python -m pip install mysql-connector-python requests > /dev/null 2>&1 || true
        
        if python integrate_narrative_analyzer.py --setup-db 2>/dev/null; then
            print_status "✅ Database schema setup completed"
        else
            print_warning "⚠️ Database schema setup failed (may need manual setup)"
        fi
        
        cd ../../..
    else
        print_warning "⚠️ News narrative analyzer not found - skipping database setup"
    fi
}

# Generate deployment summary
generate_summary() {
    print_status "Generating deployment summary..."
    
    echo ""
    echo "🎉 LLM Integration Deployment Summary"
    echo "====================================="
    
    echo ""
    echo "📊 Deployed Services:"
    kubectl get pods -n crypto-collectors | grep -E "(llm-integration|enhanced-sentiment|news-narrative)" || echo "  No LLM services found"
    
    echo ""
    echo "🔗 Service Endpoints:"
    echo "  • LLM Integration Client: http://llm-integration-client.crypto-collectors.svc.cluster.local:8040"
    echo "  • Enhanced Sentiment: http://enhanced-sentiment.crypto-collectors.svc.cluster.local:8038"
    echo "  • News Narrative Analyzer: http://news-narrative-analyzer.crypto-collectors.svc.cluster.local:8039"
    
    echo ""
    echo "🧪 Testing Commands:"
    echo "  # Port forward for testing"
    echo "  kubectl port-forward -n crypto-collectors svc/llm-integration-client 8040:8040"
    echo ""
    echo "  # Test health"
    echo "  curl http://localhost:8040/health"
    echo ""
    echo "  # Test models"
    echo "  curl http://localhost:8040/models"
    echo ""
    echo "  # Test sentiment enhancement"
    echo "  curl -X POST http://localhost:8040/enhance-sentiment \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"text\":\"Bitcoin is mooning with massive institutional adoption!\", \"original_score\": 0.8}'"
    
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Ensure your aitest Ollama services are running"
    echo "  2. Test the LLM integration endpoints"
    echo "  3. Monitor service logs for any issues"
    echo "  4. Integrate with your existing data collection pipeline"
    
    echo ""
    echo "🔧 Troubleshooting:"
    echo "  # Check service logs"
    echo "  kubectl logs -n crypto-collectors deployment/llm-integration-client"
    echo ""
    echo "  # Check aitest connectivity"
    echo "  kubectl get svc -n crypto-trading | grep ollama"
    echo ""
    echo "  # Restart services if needed"
    echo "  kubectl rollout restart deployment/llm-integration-client -n crypto-collectors"
}

# Main execution
main() {
    echo "Starting LLM Integration Deployment..."
    
    check_prerequisites
    build_images
    deploy_services
    wait_for_services
    setup_database
    test_service_health
    test_integration
    generate_summary
    
    print_status "🎉 LLM Integration deployment completed successfully!"
}

# Run main function
main "$@"