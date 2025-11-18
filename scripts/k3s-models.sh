#!/bin/bash
"""
K3s ML Models Setup and Monitoring Script

This script provides convenient functions for managing the ML models persistent storage
in the K3s crypto data collection environment.

Usage:
    ./k3s-models.sh [command]

Commands:
    setup     - Create persistent volume and run model setup job
    status    - Check status of models and setup job
    validate  - Validate models are ready and accessible
    cleanup   - Remove setup job (keeps persistent volume and models)
    reset     - Complete reset (removes everything, re-downloads models)
    logs      - Show setup job logs
    monitor   - Monitor setup progress in real-time
    help      - Show this help message
"""

set -euo pipefail

# Configuration
NAMESPACE="crypto-data-collection"
PV_NAME="ml-models-pv"
PVC_NAME="ml-models-pvc"
SETUP_JOB_NAME="ml-models-setup"
KUBECTL_CMD="kubectl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if kubectl is available and namespace exists
check_prerequisites() {
    if ! command -v $KUBECTL_CMD &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    if ! $KUBECTL_CMD get namespace $NAMESPACE &> /dev/null; then
        log_warning "Namespace $NAMESPACE not found. Creating..."
        $KUBECTL_CMD create namespace $NAMESPACE
        log_success "Namespace created"
    fi
}

# Setup persistent volume and start model download job
setup_models() {
    log_info "Setting up ML models persistent storage..."
    
    check_prerequisites
    
    # Apply persistent volume configuration
    log_info "Creating persistent volume..."
    $KUBECTL_CMD apply -f k8s/k3s-production/ml-models-storage.yaml
    
    # Wait for PVC to be bound
    log_info "Waiting for persistent volume claim to bind..."
    for i in {1..30}; do
        PVC_STATUS=$($KUBECTL_CMD get pvc $PVC_NAME -n $NAMESPACE -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
        if [ "$PVC_STATUS" = "Bound" ]; then
            log_success "Persistent volume claim bound successfully"
            break
        elif [ "$PVC_STATUS" = "NotFound" ]; then
            log_warning "PVC not found yet, waiting... (attempt $i/30)"
        else
            log_warning "PVC status: $PVC_STATUS, waiting... (attempt $i/30)"
        fi
        sleep 10
    done
    
    if [ "$PVC_STATUS" != "Bound" ]; then
        log_error "Persistent volume claim failed to bind after 5 minutes"
        log_info "Check PVC status: $KUBECTL_CMD describe pvc $PVC_NAME -n $NAMESPACE"
        exit 1
    fi
    
    # Start model setup job
    log_info "Starting model setup job..."
    $KUBECTL_CMD apply -f k8s/k3s-production/model-setup-job.yaml
    
    log_success "Model setup initiated"
    log_info "Monitor progress with: $0 monitor"
}

# Check status of models and components
check_status() {
    log_info "ML Models Setup Status"
    echo "========================"
    
    # Check persistent volume
    if $KUBECTL_CMD get pv $PV_NAME >/dev/null 2>&1; then
        PV_STATUS=$($KUBECTL_CMD get pv $PV_NAME -o jsonpath='{.status.phase}')
        log_success "Persistent Volume: $PV_STATUS"
    else
        log_error "Persistent Volume: Not found"
    fi
    
    # Check PVC
    PVC_STATUS=$($KUBECTL_CMD get pvc $PVC_NAME -n $NAMESPACE -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
    if [ "$PVC_STATUS" = "Bound" ]; then
        log_success "Persistent Volume Claim: Bound"
    else
        log_error "Persistent Volume Claim: $PVC_STATUS"
    fi
    
    # Check setup job
    if $KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE >/dev/null 2>&1; then
        JOB_STATUS=$($KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[0].type}' 2>/dev/null || echo "Unknown")
        COMPLETIONS=$($KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE -o jsonpath='{.status.completions}' 2>/dev/null || echo "0")
        
        if [ "$JOB_STATUS" = "Complete" ] && [ "$COMPLETIONS" = "1" ]; then
            log_success "Setup Job: Completed successfully"
            
            # Show completion time
            COMPLETION_TIME=$($KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE -o jsonpath='{.status.completionTime}' 2>/dev/null || echo "Unknown")
            log_info "Completed at: $COMPLETION_TIME"
        elif [ "$JOB_STATUS" = "Failed" ]; then
            log_error "Setup Job: Failed"
            FAILED_PODS=$($KUBECTL_CMD get pods -n $NAMESPACE -l job-name=$SETUP_JOB_NAME --field-selector=status.phase=Failed -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
            if [ -n "$FAILED_PODS" ]; then
                log_info "Check logs with: $0 logs"
            fi
        else
            log_warning "Setup Job: $JOB_STATUS (running or pending)"
            
            # Show active pods
            ACTIVE_PODS=$($KUBECTL_CMD get pods -n $NAMESPACE -l job-name=$SETUP_JOB_NAME --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
            if [ -n "$ACTIVE_PODS" ]; then
                log_info "Active pods: $ACTIVE_PODS"
                log_info "Monitor with: $0 monitor"
            fi
        fi
    else
        log_warning "Setup Job: Not found (run '$0 setup' to create)"
    fi
    
    # Check models in running pods
    RUNNING_PODS=$($KUBECTL_CMD get pods -n $NAMESPACE -l app=sentiment-analyzer --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [ -n "$RUNNING_PODS" ]; then
        POD=$(echo $RUNNING_PODS | cut -d' ' -f1)
        log_info "Checking model availability in pod: $POD"
        
        MODEL_COUNT=$($KUBECTL_CMD exec $POD -n $NAMESPACE -- find /app/models -name "pytorch_model.bin" 2>/dev/null | wc -l || echo "0")
        if [ "$MODEL_COUNT" -ge 3 ]; then
            log_success "Models Available: $MODEL_COUNT model files found"
            
            # Get model sizes
            MODEL_SIZES=$($KUBECTL_CMD exec $POD -n $NAMESPACE -- du -sh /app/models/* 2>/dev/null | head -5 || echo "Size info not available")
            log_info "Model sizes:"
            echo "$MODEL_SIZES" | sed 's/^/   /'
        else
            log_warning "Models Available: Only $MODEL_COUNT model files found (expected 3)"
        fi
    else
        log_warning "No running pods found to check model availability"
    fi
}

# Validate models using the Python validation script
validate_models() {
    log_info "Validating ML models..."
    
    # Find a running pod with models mounted
    RUNNING_PODS=$($KUBECTL_CMD get pods -n $NAMESPACE -l app=sentiment-analyzer --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [ -z "$RUNNING_PODS" ]; then
        log_warning "No running pods found. Checking if models exist via setup job pod..."
        
        # Try to find completed setup job pod
        SETUP_PODS=$($KUBECTL_CMD get pods -n $NAMESPACE -l job-name=$SETUP_JOB_NAME -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
        if [ -z "$SETUP_PODS" ]; then
            log_error "No pods available to validate models"
            log_info "Run '$0 setup' first or wait for services to start"
            exit 1
        fi
        POD=$(echo $SETUP_PODS | cut -d' ' -f1)
    else
        POD=$(echo $RUNNING_PODS | cut -d' ' -f1)
    fi
    
    log_info "Using pod for validation: $POD"
    
    # Run validation script
    if $KUBECTL_CMD exec $POD -n $NAMESPACE -- python scripts/validate-models.py 2>/dev/null; then
        log_success "Model validation completed successfully"
    else
        log_error "Model validation failed"
        log_info "Check pod logs: $KUBECTL_CMD logs $POD -n $NAMESPACE"
        exit 1
    fi
}

# Show setup job logs
show_logs() {
    log_info "Showing model setup job logs..."
    
    if ! $KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE >/dev/null 2>&1; then
        log_error "Setup job not found"
        exit 1
    fi
    
    # Get the most recent pod for this job
    POD=$($KUBECTL_CMD get pods -n $NAMESPACE -l job-name=$SETUP_JOB_NAME --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null)
    
    if [ -z "$POD" ]; then
        log_error "No pods found for setup job"
        exit 1
    fi
    
    log_info "Showing logs for pod: $POD"
    echo
    $KUBECTL_CMD logs $POD -n $NAMESPACE -f
}

# Monitor setup progress in real-time
monitor_setup() {
    log_info "Monitoring model setup progress..."
    
    while true; do
        clear
        echo "🔄 ML Models Setup Monitor"
        echo "=========================="
        echo "$(date)"
        echo
        
        check_status
        
        # Check if setup is complete
        if $KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE >/dev/null 2>&1; then
            JOB_STATUS=$($KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[0].type}' 2>/dev/null || echo "Unknown")
            if [ "$JOB_STATUS" = "Complete" ]; then
                echo
                log_success "🎉 Setup completed successfully!"
                break
            elif [ "$JOB_STATUS" = "Failed" ]; then
                echo
                log_error "Setup failed. Check logs with: $0 logs"
                break
            fi
        fi
        
        echo
        echo "Press Ctrl+C to stop monitoring"
        sleep 10
    done
}

# Clean up setup job (keep models and persistent volume)
cleanup_job() {
    log_info "Cleaning up model setup job..."
    
    if $KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE >/dev/null 2>&1; then
        $KUBECTL_CMD delete job $SETUP_JOB_NAME -n $NAMESPACE
        log_success "Setup job deleted"
    else
        log_info "Setup job not found (already cleaned up)"
    fi
    
    # Clean up any failed pods
    FAILED_PODS=$($KUBECTL_CMD get pods -n $NAMESPACE -l job-name=$SETUP_JOB_NAME --field-selector=status.phase=Failed -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [ -n "$FAILED_PODS" ]; then
        log_info "Cleaning up failed pods..."
        for pod in $FAILED_PODS; do
            $KUBECTL_CMD delete pod $pod -n $NAMESPACE
        done
        log_success "Failed pods cleaned up"
    fi
}

# Complete reset - remove everything and start fresh
reset_everything() {
    log_warning "This will remove all models and persistent storage!"
    read -p "Are you sure? (yes/no): " -r
    
    if [ "$REPLY" != "yes" ]; then
        log_info "Reset cancelled"
        exit 0
    fi
    
    log_info "Performing complete reset..."
    
    # Delete job first
    if $KUBECTL_CMD get job $SETUP_JOB_NAME -n $NAMESPACE >/dev/null 2>&1; then
        $KUBECTL_CMD delete job $SETUP_JOB_NAME -n $NAMESPACE --wait
        log_info "Setup job deleted"
    fi
    
    # Delete PVC
    if $KUBECTL_CMD get pvc $PVC_NAME -n $NAMESPACE >/dev/null 2>&1; then
        $KUBECTL_CMD delete pvc $PVC_NAME -n $NAMESPACE --wait
        log_info "Persistent volume claim deleted"
    fi
    
    # Delete PV
    if $KUBECTL_CMD get pv $PV_NAME >/dev/null 2>&1; then
        $KUBECTL_CMD delete pv $PV_NAME --wait
        log_info "Persistent volume deleted"
    fi
    
    log_success "Complete reset finished"
    log_info "Run '$0 setup' to start fresh"
}

# Show help
show_help() {
    echo "K3s ML Models Management Script"
    echo "==============================="
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  setup     - Create persistent volume and run model setup job"
    echo "  status    - Check status of models and setup job"
    echo "  validate  - Validate models are ready and accessible"
    echo "  cleanup   - Remove setup job (keeps persistent volume and models)"
    echo "  reset     - Complete reset (removes everything, re-downloads models)"
    echo "  logs      - Show setup job logs"
    echo "  monitor   - Monitor setup progress in real-time"
    echo "  help      - Show this help message"
    echo
    echo "Examples:"
    echo "  $0 setup     # Initial setup"
    echo "  $0 monitor   # Watch setup progress"
    echo "  $0 status    # Check current status"
    echo "  $0 validate  # Validate models are working"
    echo
    echo "Prerequisites:"
    echo "  - kubectl configured for K3s cluster"
    echo "  - Namespace 'crypto-data-collection' (created automatically)"
    echo "  - YAML files in k8s/k3s-production/ directory"
}

# Main command dispatcher
main() {
    case "${1:-help}" in
        setup)
            setup_models
            ;;
        status)
            check_status
            ;;
        validate)
            validate_models
            ;;
        logs)
            show_logs
            ;;
        monitor)
            monitor_setup
            ;;
        cleanup)
            cleanup_job
            ;;
        reset)
            reset_everything
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"