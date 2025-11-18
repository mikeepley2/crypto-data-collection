#!/bin/bash
# Test Trivy configuration locally for crypto-data-collection
# This script helps validate that Trivy scanning works with the optimized settings

set -e

echo "🔍 Testing Trivy Configuration for Crypto Data Collection"
echo "======================================================"

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo "❌ Trivy not found. Installing Trivy..."
    
    # Install Trivy based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux installation
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS installation
        brew install trivy
    else
        echo "⚠️ Please install Trivy manually: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
        exit 1
    fi
fi

echo "✅ Trivy version: $(trivy --version)"

# Test configuration files
echo ""
echo "📋 Checking configuration files..."

if [ -f "trivy.yaml" ]; then
    echo "✅ trivy.yaml found"
else
    echo "❌ trivy.yaml not found"
    exit 1
fi

if [ -f ".trivyignore" ]; then
    echo "✅ .trivyignore found"
else
    echo "❌ .trivyignore not found"
    exit 1
fi

# Test image scanning with optimized settings
IMAGE_NAME="${1:-mikeepley2/crypto-data-collection:latest}"
echo ""
echo "🔍 Testing image scan: $IMAGE_NAME"
echo "This may take a while due to large ML libraries..."

# Run Trivy with the optimized configuration
trivy image \
    --config trivy.yaml \
    --timeout 30m \
    --severity CRITICAL,HIGH,MEDIUM \
    --ignore-unfixed \
    --skip-files "**/*.so.*,**/libscipy_openblas*.so" \
    --skip-dirs "/usr/local/lib/python*/site-packages/scipy.libs" \
    --format table \
    "$IMAGE_NAME"

SCAN_RESULT=$?

echo ""
if [ $SCAN_RESULT -eq 0 ]; then
    echo "✅ Trivy scan completed successfully!"
    echo "📊 Configuration is working properly"
else
    echo "⚠️ Trivy scan completed with warnings (exit code: $SCAN_RESULT)"
    echo "🔧 This may indicate vulnerabilities found, but no timeout issues"
fi

echo ""
echo "🎯 Key optimizations applied:"
echo "   • 30-minute timeout for large ML libraries"
echo "   • Skip SciPy/NumPy binary files that cause timeouts"
echo "   • Ignore unfixed vulnerabilities"
echo "   • Focus on CRITICAL, HIGH, and MEDIUM severity"
echo "   • Include configuration and secret scanning"

echo ""
echo "📝 Next steps:"
echo "   • Review any vulnerabilities found above"
echo "   • Update base images if CRITICAL vulnerabilities exist"
echo "   • Run 'trivy image --config trivy.yaml <your-image>' to test other images"

# Test a simple filesystem scan to verify config
echo ""
echo "🗂️ Testing filesystem scan configuration..."
trivy fs --config trivy.yaml --severity CRITICAL,HIGH . || echo "⚠️ Filesystem scan completed with findings"

echo ""
echo "✅ Trivy configuration test complete!"