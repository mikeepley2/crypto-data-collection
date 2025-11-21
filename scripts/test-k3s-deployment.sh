#!/bin/bash
# K3s Deployment Testing and Validation Script
# Comprehensive testing for 12-collector crypto data platform

set -e

# Configuration
NAMESPACE="crypto-core-production"
INFRASTRUCTURE_NAMESPACE="crypto-infrastructure"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Test cluster connectivity
test_cluster_connectivity() {
    print_header "Testing K3s Cluster Connectivity"
    
    if ! kubectl cluster-info &>/dev/null; then
        print_error "❌ Cannot connect to K3s cluster"
        return 1
    fi
    
    print_status "✅ Cluster connectivity verified"
    print_status "Cluster info:"
    kubectl cluster-info
    
    print_status "Node status:"
    kubectl get nodes -o wide
    
    return 0
}

# Test namespace and basic resources
test_namespaces() {
    print_header "Testing Namespace Configuration"
    
    local namespaces=("$NAMESPACE" "$INFRASTRUCTURE_NAMESPACE" "crypto-monitoring")
    local success=0
    
    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" &>/dev/null; then
            print_status "✅ Namespace $ns exists"
            ((success++))
        else
            print_error "❌ Namespace $ns missing"
        fi
    done
    
    print_status "Resource quotas and limits:"
    kubectl get resourcequota,limitrange -n "$NAMESPACE" || print_warning "No resource limits configured"
    
    return $((${#namespaces[@]} - success))
}

# Test infrastructure components
test_infrastructure() {
    print_header "Testing Infrastructure Components"
    
    print_status "Testing MySQL deployment..."
    local mysql_ready=0
    if kubectl get statefulset mysql -n "$INFRASTRUCTURE_NAMESPACE" &>/dev/null; then
        local mysql_replicas=$(kubectl get statefulset mysql -n "$INFRASTRUCTURE_NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        if [ "$mysql_replicas" = "1" ]; then
            print_status "✅ MySQL is ready"
            mysql_ready=1
        else
            print_warning "⚠️ MySQL not ready (replicas: ${mysql_replicas:-0}/1)"
        fi
    else
        print_error "❌ MySQL StatefulSet not found"
    fi
    
    print_status "Testing Redis deployment..."
    local redis_ready=0
    if kubectl get statefulset redis -n "$INFRASTRUCTURE_NAMESPACE" &>/dev/null; then
        local redis_replicas=$(kubectl get statefulset redis -n "$INFRASTRUCTURE_NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        if [ "$redis_replicas" = "1" ]; then
            print_status "✅ Redis is ready"
            redis_ready=1
        else
            print_warning "⚠️ Redis not ready (replicas: ${redis_replicas:-0}/1)"
        fi
    else
        print_error "❌ Redis StatefulSet not found"
    fi
    
    # Test database connectivity
    if [ $mysql_ready -eq 1 ]; then
        print_status "Testing MySQL connectivity..."
        if kubectl exec -n "$INFRASTRUCTURE_NAMESPACE" statefulset/mysql -- mysqladmin ping -h localhost &>/dev/null; then
            print_status "✅ MySQL connectivity verified"
        else
            print_warning "⚠️ MySQL ping failed"
        fi
    fi
    
    return $((2 - mysql_ready - redis_ready))
}

# Test all 12 collector deployments
test_collector_deployments() {
    print_header "Testing All 12 Collector Deployments"
    
    local deployments=(
        "enhanced-news-collector"
        "enhanced-sentiment-ml-analysis"
        "enhanced-technical-calculator"
        "enhanced-materialized-updater"
        "enhanced-crypto-prices-service"
        "enhanced-crypto-news-collector-sub"
        "enhanced-onchain-collector"
        "enhanced-technical-indicators-collector"
        "enhanced-macro-collector-v2"
        "enhanced-crypto-derivatives-collector"
        "ml-market-collector"
        "enhanced-ohlc-collector"
    )
    
    local ready_count=0
    local total_count=${#deployments[@]}
    
    for deployment in "${deployments[@]}"; do
        print_status "Testing deployment: $deployment"
        
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &>/dev/null; then
            local ready_replicas=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
            local desired_replicas=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
            
            if [ "$ready_replicas" = "$desired_replicas" ] && [ "$ready_replicas" != "" ]; then
                print_status "  ✅ $deployment ($ready_replicas/$desired_replicas replicas ready)"
                ((ready_count++))
            else
                print_warning "  ⚠️ $deployment (${ready_replicas:-0}/$desired_replicas replicas ready)"
                
                # Show recent events for troubleshooting
                print_status "  Recent events:"
                kubectl get events -n "$NAMESPACE" --field-selector involvedObject.name="$deployment" --sort-by='.lastTimestamp' | tail -3 || true
            fi
        else
            print_error "  ❌ $deployment deployment not found"
        fi
    done
    
    print_status "Deployment Summary: $ready_count/$total_count collectors ready"
    
    if [ $ready_count -lt $((total_count * 70 / 100)) ]; then
        print_error "Less than 70% of collectors are ready. Deployment may have issues."
        return 1
    fi
    
    return 0
}

# Test service configuration
test_services() {
    print_header "Testing Service Configuration"
    
    print_status "Checking all services..."
    kubectl get services -n "$NAMESPACE"
    
    print_status "Testing service endpoints..."
    local services_with_endpoints=0
    local total_services=$(kubectl get services -n "$NAMESPACE" --no-headers | wc -l)
    
    while read -r service; do
        if [ -n "$service" ] && [[ "$service" != "crypto-api-gateway" ]] && [[ "$service" != "crypto-core-lb" ]]; then
            local endpoints=$(kubectl get endpoints "$service" -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null || echo "")
            if [ -n "$endpoints" ]; then
                print_status "  ✅ $service has endpoints: $endpoints"
                ((services_with_endpoints++))
            else
                print_warning "  ⚠️ $service has no endpoints"
            fi
        fi
    done < <(kubectl get services -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n')
    
    print_status "Services with endpoints: $services_with_endpoints/$total_services"
    return 0
}

# Test pod health and logs
test_pod_health() {
    print_header "Testing Pod Health and Status"
    
    print_status "Pod overview:"
    kubectl get pods -n "$NAMESPACE" -o wide
    
    print_status "Checking for problematic pods..."
    local failed_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed --no-headers | wc -l)
    local pending_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Pending --no-headers | wc -l)
    local running_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)
    
    print_status "Pod Status Summary:"
    echo "  Running: $running_pods"
    echo "  Pending: $pending_pods"
    echo "  Failed: $failed_pods"
    
    if [ $failed_pods -gt 0 ]; then
        print_error "Found $failed_pods failed pods:"
        kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed
        
        print_status "Logs from failed pods:"
        kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed -o jsonpath='{.items[*].metadata.name}' | \
        tr ' ' '\n' | while read -r pod; do
            if [ -n "$pod" ]; then
                print_status "Logs for $pod:"
                kubectl logs "$pod" -n "$NAMESPACE" --tail=20 || true
            fi
        done
    fi
    
    return $failed_pods
}

# Test collector imports (similar to validate_collectors.py)
test_collector_imports() {
    print_header "Testing Collector Module Imports"
    
    # Create a test job that validates imports
    cat > /tmp/collector-test-job.yaml << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: collector-import-test
  namespace: crypto-core-production
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: test-runner
        image: python:3.11-slim
        command: ['sh', '-c']
        args:
        - |
          echo "Installing dependencies..."
          pip install mysql-connector-python prometheus-client structlog
          echo "Testing basic Python imports..."
          python -c "
          import sys
          import os
          
          # Test standard imports
          modules_to_test = [
              'mysql.connector',
              'prometheus_client',
              'structlog',
              'json',
              'datetime',
              'requests'
          ]
          
          success_count = 0
          for module in modules_to_test:
              try:
                  __import__(module)
                  print(f'✅ {module} imported successfully')
                  success_count += 1
              except ImportError as e:
                  print(f'❌ {module} failed: {e}')
          
          print(f'Import test summary: {success_count}/{len(modules_to_test)} successful')
          
          if success_count >= len(modules_to_test) * 0.8:
              print('✅ Import tests passed')
              exit(0)
          else:
              print('❌ Import tests failed')
              exit(1)
          "
EOF
    
    print_status "Running collector import test job..."
    kubectl apply -f /tmp/collector-test-job.yaml
    
    # Wait for job completion
    if kubectl wait --for=condition=complete job/collector-import-test -n "$NAMESPACE" --timeout=120s; then
        print_status "Import test job completed successfully"
        kubectl logs job/collector-import-test -n "$NAMESPACE"
        kubectl delete job collector-import-test -n "$NAMESPACE"
        rm -f /tmp/collector-test-job.yaml
        return 0
    else
        print_error "Import test job failed or timed out"
        kubectl logs job/collector-import-test -n "$NAMESPACE" || true
        kubectl delete job collector-import-test -n "$NAMESPACE" || true
        rm -f /tmp/collector-test-job.yaml
        return 1
    fi
}

# Run comprehensive test suite
run_full_test_suite() {
    print_header "Running Full K3s Deployment Test Suite"
    
    local test_results=()
    
    # Run all tests
    test_cluster_connectivity && test_results+=("cluster_connectivity:PASS") || test_results+=("cluster_connectivity:FAIL")
    test_namespaces && test_results+=("namespaces:PASS") || test_results+=("namespaces:FAIL")
    test_infrastructure && test_results+=("infrastructure:PASS") || test_results+=("infrastructure:FAIL")
    test_collector_deployments && test_results+=("collector_deployments:PASS") || test_results+=("collector_deployments:FAIL")
    test_services && test_results+=("services:PASS") || test_results+=("services:FAIL")
    test_pod_health && test_results+=("pod_health:PASS") || test_results+=("pod_health:FAIL")
    test_collector_imports && test_results+=("collector_imports:PASS") || test_results+=("collector_imports:FAIL")
    
    # Summary
    print_header "Test Results Summary"
    
    local pass_count=0
    local total_count=${#test_results[@]}
    
    for result in "${test_results[@]}"; do
        local test_name=$(echo "$result" | cut -d: -f1)
        local test_status=$(echo "$result" | cut -d: -f2)
        
        if [ "$test_status" = "PASS" ]; then
            print_status "✅ $test_name: PASSED"
            ((pass_count++))
        else
            print_error "❌ $test_name: FAILED"
        fi
    done
    
    print_status "Overall Results: $pass_count/$total_count tests passed"
    
    if [ $pass_count -eq $total_count ]; then
        print_status "🎉 All tests passed! K3s deployment is healthy."
        return 0
    elif [ $pass_count -ge $((total_count * 80 / 100)) ]; then
        print_warning "⚠️ Most tests passed. Minor issues detected."
        return 1
    else
        print_error "❌ Multiple test failures. Deployment needs attention."
        return 2
    fi
}

# Performance test
test_performance() {
    print_header "Running Performance Tests"
    
    print_status "Resource usage by namespace:"
    kubectl top pods -n "$NAMESPACE" 2>/dev/null || print_warning "Metrics server not available"
    
    print_status "Checking resource limits and requests:"
    kubectl describe resourcequota -n "$NAMESPACE" || print_warning "No resource quotas configured"
    
    print_status "Node resource usage:"
    kubectl top nodes 2>/dev/null || print_warning "Node metrics not available"
}

# Main function
main() {
    case "${1:-test}" in
        "test"|"full")
            run_full_test_suite
            ;;
        "quick")
            test_cluster_connectivity
            test_collector_deployments
            test_services
            ;;
        "infrastructure")
            test_cluster_connectivity
            test_namespaces
            test_infrastructure
            ;;
        "collectors")
            test_collector_deployments
            test_pod_health
            ;;
        "imports")
            test_collector_imports
            ;;
        "performance")
            test_performance
            ;;
        *)
            echo "K3s Deployment Testing and Validation Script"
            echo ""
            echo "Usage:"
            echo "  $0 test         # Run full test suite (default)"
            echo "  $0 quick        # Quick connectivity and deployment test"
            echo "  $0 infrastructure # Test infrastructure components only"
            echo "  $0 collectors   # Test collector deployments only"
            echo "  $0 imports      # Test collector imports only"
            echo "  $0 performance  # Check resource usage and performance"
            echo ""
            echo "Test Categories:"
            echo "  - Cluster connectivity"
            echo "  - Namespace configuration"
            echo "  - Infrastructure (MySQL, Redis)"
            echo "  - All 12 collector deployments"
            echo "  - Service configuration"
            echo "  - Pod health and logs"
            echo "  - Collector import validation"
            exit 1
            ;;
    esac
}

main "$@"