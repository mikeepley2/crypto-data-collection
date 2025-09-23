#!/bin/bash

# Initialize Crypto Data Collection Repository
# This script sets up the Git repository and prepares it for development

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

main() {
    log "Initializing Crypto Data Collection repository..."
    
    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "src" ]; then
        echo "❌ Please run this script from the crypto-data-collection directory"
        exit 1
    fi
    
    # Initialize Git repository
    if [ ! -d ".git" ]; then
        log "Initializing Git repository..."
        git init
        success "Git repository initialized"
    else
        success "Git repository already exists"
    fi
    
    # Make scripts executable
    log "Making scripts executable..."
    chmod +x scripts/*.sh
    success "Scripts are now executable"
    
    # Set up Python virtual environment
    if [ ! -d "venv" ]; then
        log "Creating Python virtual environment..."
        python -m venv venv
        success "Virtual environment created"
        
        log "Installing Python dependencies..."
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
            ./venv/Scripts/pip install -r requirements.txt
        else
            ./venv/bin/pip install -r requirements.txt
        fi
        success "Dependencies installed"
    else
        success "Virtual environment already exists"
    fi
    
    # Stage all files for initial commit
    log "Staging files for Git..."
    git add .
    
    # Create initial commit if needed
    if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
        log "Creating initial commit..."
        git commit -m "Initial commit: Isolated crypto data collection system

Features:
- Dedicated data collection services isolated from trading system
- Unified API gateway for data access
- Kubernetes deployment manifests
- Windows MySQL integration via host.docker.internal
- Comprehensive documentation and development setup"
        success "Initial commit created"
    else
        success "Repository already has commits"
    fi
    
    # Display next steps
    echo
    echo "================================================================="
    echo "🎉 CRYPTO DATA COLLECTION REPOSITORY INITIALIZED"
    echo "================================================================="
    echo
    echo "📁 Repository Structure:"
    echo "   ├── src/           # Source code (API Gateway, Collectors, Processing)"
    echo "   ├── k8s/           # Kubernetes manifests"
    echo "   ├── scripts/       # Deployment and management scripts"
    echo "   ├── docs/          # Documentation"
    echo "   └── tests/         # Test suites"
    echo
    echo "🚀 Next Steps:"
    echo
    echo "1. 📝 Configure API Keys:"
    echo "   Edit k8s/02-secrets.yaml with your actual API keys"
    echo
    echo "2. 🔗 Add GitHub Remote:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/crypto-data-collection.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo
    echo "3. 🖥️ Open VSCode Workspace:"
    echo "   code crypto-data-collection.code-workspace"
    echo
    echo "4. 🚀 Deploy to Kubernetes:"
    echo "   ./scripts/deploy.sh"
    echo
    echo "5. ✅ Validate Deployment:"
    echo "   ./scripts/validate.sh"
    echo
    echo "📚 Documentation:"
    echo "   • API Reference: docs/api.md"
    echo "   • Repository Setup: REPOSITORY_SETUP.md"
    echo "   • Windows DB Integration: WINDOWS_DATABASE_INTEGRATION.md"
    echo
    echo "🎯 This isolated data collection system ensures:"
    echo "   ✅ Zero impact on live trading operations"
    echo "   ✅ Independent scaling and deployment"
    echo "   ✅ Clean separation of concerns"
    echo "   ✅ Unified data access via APIs"
    echo "================================================================="
}

main "$@"