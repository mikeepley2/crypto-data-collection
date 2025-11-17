#!/bin/bash

# ============================================================================
# Containerized Test Runner for CI/CD
# ============================================================================
# Runs all tests in containers - no local environment dependencies
# Perfect for CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins, etc.)

set -e  # Exit on error

echo "🐳 CONTAINERIZED TEST SUITE"
echo "=" * 60
echo "🛡️  SAFETY: Fully isolated containerized testing"
echo "🚀 CI/CD Ready: No local dependencies required"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Parse command line arguments
TEST_TYPE=${1:-"all"}

# Check if Docker is available
if ! command -v docker-compose &> /dev/null; then
    error "docker-compose is not installed or not in PATH"
    exit 1
fi

# For CI environments, just run pytest directly
log "🧪 Running tests with pytest..."

case "$TEST_TYPE" in
    "unit")
        log "🔗 Running Unit Tests Only"
        python -m pytest tests/ -v --tb=short -x --disable-warnings
        ;;
    "integration")
        log "🔗 Running Integration Tests"
        python -m pytest tests/test_pytest_comprehensive_integration.py -v --tb=short
        ;;
    "all")
        log "🚀 Running Full Test Suite"
        python -m pytest tests/ -v --tb=short
        ;;
    *)
        error "Unknown test type: $TEST_TYPE"
        log "Available test types: unit, integration, all"
        exit 1
        ;;
esac

TEST_RESULT=$?

log "📋 Test execution completed..."

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    success "🎉 ALL TESTS PASSED!"
    echo "   ✅ Test suite completed successfully"
    echo "   ✅ CI/CD ready"
else
    echo ""
    error "❌ Tests failed"
    echo "   Check the output above for details"
fi

exit $TEST_RESULT
