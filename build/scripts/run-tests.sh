#!/bin/bash

# Run Tests Script
# Comprehensive testing script for the crypto data collection system

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Default values
TEST_TYPE="all"
COVERAGE="false"
PARALLEL="false"
VERBOSE="false"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE="true"
            shift
            ;;
        -p|--parallel)
            PARALLEL="true"
            shift
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Show usage
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE     Test type (unit|integration|performance|all) [default: all]"
    echo "  -c, --coverage      Generate coverage report"
    echo "  -p, --parallel      Run tests in parallel"
    echo "  -v, --verbose       Verbose output"
    echo "  -h, --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run all tests"
    echo "  $0 -t unit -c                # Run unit tests with coverage"
    echo "  $0 -t integration -v         # Run integration tests verbosely"
    echo "  $0 -p -c                     # Run all tests in parallel with coverage"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    cd "$PROJECT_ROOT"
    
    # Check Python
    if ! command -v python >/dev/null 2>&1; then
        log_error "Python not found"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        log_info "Creating virtual environment..."
        python -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
    
    # Install test dependencies
    log_info "Installing test dependencies..."
    pip install -q pytest pytest-asyncio pytest-mock pytest-cov pytest-xdist pytest-benchmark
}

# Setup test environment
setup_test_env() {
    export ENVIRONMENT=test
    export DB_HOST=localhost
    export DB_USER=test
    export DB_PASSWORD=test
    export DB_NAME=test_db
    export REDIS_HOST=localhost
    export REDIS_PORT=6379
}

# Run unit tests
run_unit_tests() {
    log_info "Running unit tests..."
    
    local pytest_args=()
    
    # Basic arguments
    pytest_args+=("tests/")
    pytest_args+=("-m" "not integration and not performance")
    
    # Verbose output
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-v")
    fi
    
    # Coverage
    if [[ "$COVERAGE" == "true" ]]; then
        pytest_args+=("--cov=services")
        pytest_args+=("--cov=templates")
        pytest_args+=("--cov-report=html")
        pytest_args+=("--cov-report=xml")
        pytest_args+=("--cov-report=term-missing")
    fi
    
    # Parallel execution
    if [[ "$PARALLEL" == "true" ]]; then
        pytest_args+=("-n" "auto")
    fi
    
    # JUnit XML output
    pytest_args+=("--junitxml=test-results-unit.xml")
    
    if pytest "${pytest_args[@]}"; then
        log_success "Unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."
    
    # Check if test database is available
    if ! check_test_database; then
        log_warning "Test database not available, skipping integration tests"
        return 0
    fi
    
    local pytest_args=()
    
    pytest_args+=("tests/")
    pytest_args+=("-m" "integration")
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-v")
    fi
    
    pytest_args+=("--junitxml=test-results-integration.xml")
    
    if pytest "${pytest_args[@]}"; then
        log_success "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Run performance tests
run_performance_tests() {
    log_info "Running performance tests..."
    
    local pytest_args=()
    
    pytest_args+=("tests/")
    pytest_args+=("-m" "performance")
    pytest_args+=("--benchmark-json=benchmark-results.json")
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-v")
    fi
    
    if pytest "${pytest_args[@]}"; then
        log_success "Performance tests passed"
        return 0
    else
        log_error "Performance tests failed"
        return 1
    fi
}

# Check test database availability
check_test_database() {
    # Try to connect to test database
    python -c "
import asyncio
import asyncpg
import sys

async def check_db():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='test',
            password='test',
            database='test_db',
            command_timeout=5
        )
        await conn.close()
        return True
    except:
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
" >/dev/null 2>&1
}

# Generate test report
generate_report() {
    log_info "Generating test report..."
    
    echo "# Test Report" > test-report.md
    echo "Generated at: $(date)" >> test-report.md
    echo "" >> test-report.md
    
    # Unit test results
    if [[ -f "test-results-unit.xml" ]]; then
        echo "## Unit Tests" >> test-report.md
        python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('test-results-unit.xml')
    root = tree.getroot()
    tests = root.get('tests', '0')
    failures = root.get('failures', '0')
    errors = root.get('errors', '0')
    time = root.get('time', '0')
    print(f'- Tests: {tests}')
    print(f'- Failures: {failures}')
    print(f'- Errors: {errors}')
    print(f'- Duration: {time}s')
except:
    print('- Results not available')
" >> test-report.md
        echo "" >> test-report.md
    fi
    
    # Integration test results
    if [[ -f "test-results-integration.xml" ]]; then
        echo "## Integration Tests" >> test-report.md
        python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('test-results-integration.xml')
    root = tree.getroot()
    tests = root.get('tests', '0')
    failures = root.get('failures', '0')
    errors = root.get('errors', '0')
    time = root.get('time', '0')
    print(f'- Tests: {tests}')
    print(f'- Failures: {failures}')
    print(f'- Errors: {errors}')
    print(f'- Duration: {time}s')
except:
    print('- Results not available')
" >> test-report.md
        echo "" >> test-report.md
    fi
    
    # Coverage report
    if [[ "$COVERAGE" == "true" ]] && [[ -f "htmlcov/index.html" ]]; then
        echo "## Coverage Report" >> test-report.md
        echo "Coverage report available at: htmlcov/index.html" >> test-report.md
        echo "" >> test-report.md
    fi
    
    log_success "Test report generated: test-report.md"
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    log_info "Starting test execution..."
    log_info "Test type: $TEST_TYPE"
    log_info "Coverage: $COVERAGE"
    log_info "Parallel: $PARALLEL"
    log_info "Verbose: $VERBOSE"
    echo
    
    check_prerequisites
    setup_test_env
    
    local exit_code=0
    
    case "$TEST_TYPE" in
        unit)
            run_unit_tests || exit_code=1
            ;;
        integration)
            run_integration_tests || exit_code=1
            ;;
        performance)
            run_performance_tests || exit_code=1
            ;;
        all)
            run_unit_tests || exit_code=1
            run_integration_tests || exit_code=1
            run_performance_tests || exit_code=1
            ;;
        *)
            log_error "Invalid test type: $TEST_TYPE"
            usage
            ;;
    esac
    
    generate_report
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "All tests completed successfully!"
    else
        log_error "Some tests failed!"
    fi
    
    exit $exit_code
}

main "$@"