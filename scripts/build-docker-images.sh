#!/bin/bash
# Docker Build Script for All 12 Crypto Data Collectors
# Builds container images for K3s deployment

set -e

# Configuration
DOCKER_REGISTRY="localhost:5000"  # Local K3s registry
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_TAG="latest"

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

# Function to create Dockerfile for Python collectors
create_python_dockerfile() {
    local collector_name="$1"
    local collector_path="$2"
    local port="$3"
    local dockerfile_path="$4"
    local requirements_type="${5:-base}"  # base, ml, or financial
    
    cat > "$dockerfile_path" << EOF
FROM python:3.11-slim

LABEL maintainer="crypto-data-collection"
LABEL service="$collector_name"

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-${requirements_type}.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Copy shared modules first
COPY shared/ ./shared/

# Copy service-specific code
COPY $collector_path ./

# Copy the main collector module
COPY *.py ./

# Set Python path
ENV PYTHONPATH="/app:/app/shared"

# Expose port
EXPOSE $port

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD python -c "import $collector_name; print('OK')" || exit 1

# Run the collector
CMD ["python", "-m", "$collector_name"]
EOF
}

# Function to build Docker image
build_docker_image() {
    local image_name="$1"
    local dockerfile_path="$2"
    local build_context="$3"
    
    print_status "Building Docker image: $image_name"
    
    if docker build -f "$dockerfile_path" -t "$image_name:$BUILD_TAG" "$build_context"; then
        print_status "✅ Successfully built $image_name"
        
        # Tag for local registry if available
        if docker info | grep -q "Registry"; then
            docker tag "$image_name:$BUILD_TAG" "$DOCKER_REGISTRY/$image_name:$BUILD_TAG"
            print_status "Tagged for registry: $DOCKER_REGISTRY/$image_name:$BUILD_TAG"
        fi
        
        return 0
    else
        print_error "❌ Failed to build $image_name"
        return 1
    fi
}

# Build all collectors
build_all_collectors() {
    print_header "Building All 12 Crypto Data Collectors"
    
    # Change to project directory
    cd "$PROJECT_ROOT" || {
        print_error "Project directory not found: $PROJECT_ROOT"
        exit 1
    }
    
    local build_errors=0
    
    # 1. Enhanced News Collector (Top-level) - BASE
    print_status "Building Enhanced News Collector (Top-level)..."
    create_python_dockerfile "enhanced_news_collector" "." "8001" "Dockerfile.enhanced-news-collector" "base"
    build_docker_image "crypto-enhanced-news-collector" "Dockerfile.enhanced-news-collector" "." || ((build_errors++))
    
    # 2. Enhanced Sentiment ML Analysis - ML
    print_status "Building Enhanced Sentiment ML Analysis..."
    create_python_dockerfile "enhanced_sentiment_ml_analysis" "." "8002" "Dockerfile.enhanced-sentiment-ml" "ml"
    build_docker_image "crypto-enhanced-sentiment-ml" "Dockerfile.enhanced-sentiment-ml" "." || ((build_errors++))
    
    # 3. Enhanced Technical Calculator - FINANCIAL
    print_status "Building Enhanced Technical Calculator..."
    create_python_dockerfile "enhanced_technical_calculator" "." "8003" "Dockerfile.enhanced-technical-calculator" "financial"
    build_docker_image "crypto-enhanced-technical-calculator" "Dockerfile.enhanced-technical-calculator" "." || ((build_errors++))
    
    # 4. Enhanced Materialized Updater - BASE
    print_status "Building Enhanced Materialized Updater..."
    create_python_dockerfile "enhanced_materialized_updater_template" "." "8004" "Dockerfile.enhanced-materialized-updater" "base"
    build_docker_image "crypto-enhanced-materialized-updater" "Dockerfile.enhanced-materialized-updater" "." || ((build_errors++))
    
    # 5. Enhanced Crypto Prices Service (subdirectory) - BASE
    print_status "Building Enhanced Crypto Prices Service..."
    create_python_dockerfile "enhanced_crypto_prices_service" "services/price-collection" "8005" "Dockerfile.enhanced-prices-service" "base"
    build_docker_image "crypto-enhanced-prices-service" "Dockerfile.enhanced-prices-service" "." || ((build_errors++))
    
    # 6. Enhanced Crypto News Collector (subdirectory) - BASE
    print_status "Building Enhanced Crypto News Collector (Subdirectory)..."
    create_python_dockerfile "enhanced_crypto_news_collector" "services/news-collection" "8006" "Dockerfile.enhanced-news-collector-sub" "base"
    build_docker_image "crypto-enhanced-news-collector-sub" "Dockerfile.enhanced-news-collector-sub" "." || ((build_errors++))
    
    # 7. Enhanced Onchain Collector - BASE
    print_status "Building Enhanced Onchain Collector..."
    create_python_dockerfile "enhanced_onchain_collector" "services/onchain-collection" "8007" "Dockerfile.enhanced-onchain-collector" "base"
    build_docker_image "crypto-enhanced-onchain-collector" "Dockerfile.enhanced-onchain-collector" "." || ((build_errors++))
    
    # 8. Enhanced Technical Indicators Collector - FINANCIAL
    print_status "Building Enhanced Technical Indicators Collector..."
    create_python_dockerfile "enhanced_technical_indicators_collector" "services/technical-collection" "8008" "Dockerfile.enhanced-technical-indicators" "financial"
    build_docker_image "crypto-enhanced-technical-indicators" "Dockerfile.enhanced-technical-indicators" "." || ((build_errors++))
    
    # 9. Enhanced Macro Collector V2 - BASE
    print_status "Building Enhanced Macro Collector V2..."
    create_python_dockerfile "enhanced_macro_collector_v2" "services/macro-collection" "8009" "Dockerfile.enhanced-macro-collector-v2" "base"
    build_docker_image "crypto-enhanced-macro-collector-v2" "Dockerfile.enhanced-macro-collector-v2" "." || ((build_errors++))
    
    # 10. Enhanced Crypto Derivatives Collector - BASE
    print_status "Building Enhanced Crypto Derivatives Collector..."
    create_python_dockerfile "enhanced_crypto_derivatives_collector" "services/derivatives-collection" "8010" "Dockerfile.enhanced-derivatives-collector" "base"
    build_docker_image "crypto-enhanced-derivatives-collector" "Dockerfile.enhanced-derivatives-collector" "." || ((build_errors++))
    
    # 11. ML Market Collector - BASE
    print_status "Building ML Market Collector..."
    create_python_dockerfile "ml_market_collector" "services/market-collection" "8011" "Dockerfile.ml-market-collector" "base"
    build_docker_image "crypto-ml-market-collector" "Dockerfile.ml-market-collector" "." || ((build_errors++))
    
    # 12. Enhanced OHLC Collector - FINANCIAL
    print_status "Building Enhanced OHLC Collector..."
    create_python_dockerfile "enhanced_ohlc_collector" "services/ohlc-collection" "8012" "Dockerfile.enhanced-ohlc-collector" "financial"
    build_docker_image "crypto-enhanced-ohlc-collector" "Dockerfile.enhanced-ohlc-collector" "." || ((build_errors++))
    
    # Summary
    print_header "Build Summary"
    if [ $build_errors -eq 0 ]; then
        print_status "🎉 All 12 collectors built successfully!"
        
        print_status "Available Docker images:"
        docker images | grep crypto-
        
        print_status "Next steps:"
        echo "  1. Push images to registry: ./scripts/push-images-to-k3s.sh"
        echo "  2. Deploy to K3s: ./scripts/deploy-to-k3s.sh deploy"
        
    else
        print_error "❌ $build_errors collectors failed to build"
        print_warning "Check the errors above and fix before deployment"
        exit 1
    fi
}

# Push images to K3s local registry
push_to_registry() {
    print_header "Pushing Images to K3s Registry"
    
    if ! docker info | grep -q "Registry"; then
        print_warning "No local registry detected. Images will be available locally only."
        return 0
    fi
    
    local push_errors=0
    local images=(
        "crypto-enhanced-news-collector"
        "crypto-enhanced-sentiment-ml"
        "crypto-enhanced-technical-calculator"
        "crypto-enhanced-materialized-updater"
        "crypto-enhanced-prices-service"
        "crypto-enhanced-news-collector-sub"
        "crypto-enhanced-onchain-collector"
        "crypto-enhanced-technical-indicators"
        "crypto-enhanced-macro-collector-v2"
        "crypto-enhanced-derivatives-collector"
        "crypto-ml-market-collector"
        "crypto-enhanced-ohlc-collector"
    )
    
    for image in "${images[@]}"; do
        print_status "Pushing $image to registry..."
        if docker push "$DOCKER_REGISTRY/$image:$BUILD_TAG"; then
            print_status "✅ $image pushed successfully"
        else
            print_error "❌ Failed to push $image"
            ((push_errors++))
        fi
    done
    
    if [ $push_errors -eq 0 ]; then
        print_status "🎉 All images pushed to registry successfully!"
    else
        print_error "❌ $push_errors images failed to push"
    fi
}

# Cleanup function
cleanup_build_files() {
    print_status "Cleaning up build files..."
    rm -f Dockerfile.* 2>/dev/null || true
    print_status "✅ Cleanup complete"
}

# Main function
main() {
    case "${1:-build}" in
        "build")
            build_all_collectors
            ;;
        "push")
            push_to_registry
            ;;
        "all")
            build_all_collectors
            push_to_registry
            ;;
        "cleanup")
            cleanup_build_files
            ;;
        *)
            echo "Docker Build Script for Crypto Data Collectors"
            echo ""
            echo "Usage:"
            echo "  $0 build     # Build all 12 collector Docker images"
            echo "  $0 push      # Push built images to K3s registry"
            echo "  $0 all       # Build and push images"
            echo "  $0 cleanup   # Clean up generated Dockerfiles"
            echo ""
            echo "Prerequisites:"
            echo "  - Docker must be installed and running"
            echo "  - All collector source code must be present"
            echo "  - requirements.txt files must exist"
            exit 1
            ;;
    esac
}

main "$@"