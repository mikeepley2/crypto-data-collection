#!/bin/bash

# Ollama LLM Service Setup Script
set -e

echo "🚀 Setting up Ollama LLM Service for Crypto Data Enhancement"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "ollama_service.py" ]]; then
    print_error "Please run this script from the ollama_llm directory"
    exit 1
fi

print_status "Building Ollama LLM Service Docker image..."
docker build -t ollama-llm-service:latest .

print_status "Starting Ollama server with Docker Compose..."
docker-compose up -d ollama

# Wait for Ollama to be ready
print_status "Waiting for Ollama server to be ready..."
timeout=120
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_status "✅ Ollama server is ready!"
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "Waiting... ($elapsed/$timeout seconds)"
done

if [ $elapsed -ge $timeout ]; then
    print_error "Ollama server failed to start within $timeout seconds"
    exit 1
fi

# Pull required models
print_status "Pulling required Ollama models..."

models=("llama3.2:3b" "mistral:7b" "deepseek-coder:6.7b" "qwen2.5:7b")

for model in "${models[@]}"; do
    print_status "Pulling $model..."
    if docker exec ollama-server ollama pull "$model"; then
        print_status "✅ Successfully pulled $model"
    else
        print_warning "⚠️ Failed to pull $model, continuing..."
    fi
done

print_status "Starting Ollama LLM Service..."
docker-compose up -d ollama-llm-service

# Wait for service to be ready
print_status "Waiting for LLM service to be ready..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -s http://localhost:8037/health > /dev/null 2>&1; then
        print_status "✅ Ollama LLM Service is ready!"
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "Waiting... ($elapsed/$timeout seconds)"
done

if [ $elapsed -ge $timeout ]; then
    print_error "LLM service failed to start within $timeout seconds"
    docker-compose logs ollama-llm-service
    exit 1
fi

# Test the service
print_status "Testing Ollama LLM Service endpoints..."

# Test health endpoint
if curl -s http://localhost:8037/health | grep -q "healthy"; then
    print_status "✅ Health endpoint working"
else
    print_warning "⚠️ Health endpoint may have issues"
fi

# Test models endpoint
if curl -s http://localhost:8037/models | grep -q "models"; then
    print_status "✅ Models endpoint working"
else
    print_warning "⚠️ Models endpoint may have issues"
fi

print_status "🎉 Ollama LLM Service setup complete!"
echo ""
echo "🔗 Service endpoints:"
echo "   Health: http://localhost:8037/health"
echo "   Models: http://localhost:8037/models"
echo "   Docs:   http://localhost:8037/docs"
echo ""
echo "🔧 Service features:"
echo "   • Enhanced sentiment analysis"
echo "   • Market narrative extraction"
echo "   • Technical pattern recognition"
echo "   • Market regime classification"
echo ""
echo "📊 Next steps:"
echo "   1. Test the enhanced sentiment API"
echo "   2. Integrate with existing sentiment service"
echo "   3. Set up automated market analysis"

# Optional: Deploy to Kubernetes if requested
read -p "Deploy to Kubernetes cluster? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Deploying to Kubernetes..."
    kubectl apply -f k8s-deployment.yaml
    
    print_status "Waiting for Kubernetes deployment..."
    kubectl wait --for=condition=available --timeout=300s deployment/ollama-server -n crypto-collectors
    kubectl wait --for=condition=available --timeout=300s deployment/ollama-llm-service -n crypto-collectors
    
    print_status "✅ Kubernetes deployment complete!"
    
    # Port forward for testing
    print_status "Setting up port forwarding for testing..."
    kubectl port-forward -n crypto-collectors svc/ollama-llm-service 8037:8037 &
    
    echo "🌐 Kubernetes service available at http://localhost:8037"
fi

print_status "🚀 Setup complete! Ollama LLM Service is ready for crypto data enhancement."