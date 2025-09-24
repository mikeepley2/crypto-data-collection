#!/bin/bash
# Master Service Management Script
# ===============================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="crypto-collectors"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_menu() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        CRYPTO SERVICE MANAGEMENT SUITE        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
    echo
    echo "Select an option:"
    echo
    echo "  1) 📊 Real-time Dashboard"
    echo "  2) 🔍 Health Check & Report"
    echo "  3) 🧹 Clean up Failed Resources"
    echo "  4) 🔧 Run Comprehensive Maintenance"
    echo "  5) 🚀 Safe Service Update"
    echo "  6) 📏 Scale Service"
    echo "  7) 🔌 Circuit Breaker Check"
    echo "  8) 📋 Generate Health Report"
    echo "  9) 🔄 Validate Data Flow"
    echo " 10) 🚨 Setup Monitoring Alerts"
    echo " 11) ⚙️  Deploy Service Management Tools"
    echo " 12) 📖 Show Best Practices Guide"
    echo
    echo "  0) Exit"
    echo
    read -p "Enter your choice [0-12]: " choice
}

deploy_management_tools() {
    echo -e "${BLUE}🚀 Deploying service management tools...${NC}"
    
    # Apply cleanup CronJob
    if [ -f "$SCRIPT_DIR/../service-health-management.yaml" ]; then
        kubectl apply -f "$SCRIPT_DIR/../service-health-management.yaml"
        echo "✅ Automated cleanup CronJob deployed"
    fi
    
    # Apply monitoring setup
    if [ -f "$SCRIPT_DIR/../monitoring-setup.yaml" ]; then
        kubectl apply -f "$SCRIPT_DIR/../monitoring-setup.yaml"
        echo "✅ Monitoring system deployed"
    fi
    
    # Apply RBAC for cleanup
    if [ -f "$SCRIPT_DIR/../pod-cleanup-rbac.yaml" ]; then
        kubectl apply -f "$SCRIPT_DIR/../pod-cleanup-rbac.yaml"
        echo "✅ RBAC permissions configured"
    fi
    
    echo -e "${GREEN}✅ All management tools deployed successfully!${NC}"
}

show_best_practices() {
    clear
    echo -e "${BLUE}📖 SERVICE MANAGEMENT BEST PRACTICES${NC}"
    echo "════════════════════════════════════════════════"
    echo
    echo "🏥 HEALTH MANAGEMENT:"
    echo "  • Always configure liveness and readiness probes"
    echo "  • Set appropriate resource requests and limits"
    echo "  • Use startup probes for slow-starting services"
    echo "  • Monitor restart counts and investigate high restarts"
    echo
    echo "🔄 DEPLOYMENT STRATEGIES:"
    echo "  • Use rolling updates with maxUnavailable: 0 for critical services"
    echo "  • Test deployments in staging before production"
    echo "  • Always have rollback plan ready"
    echo "  • Use canary deployments for major changes"
    echo
    echo "🧹 CLEANUP & MAINTENANCE:"
    echo "  • Run automated cleanup every 6 hours"
    echo "  • Monitor resource usage trends"
    echo "  • Remove old jobs and failed pods regularly"
    echo "  • Keep logs for debugging but rotate them"
    echo
    echo "📊 MONITORING:"
    echo "  • Set up alerts for pod restarts"
    echo "  • Monitor data collection rates"
    echo "  • Track resource utilization over time"
    echo "  • Alert on service downtime > 5 minutes"
    echo
    echo "🔧 TROUBLESHOOTING:"
    echo "  • Check pod logs first: kubectl logs <pod>"
    echo "  • Verify service connectivity: kubectl get svc"
    echo "  • Check resource constraints: kubectl top pods"
    echo "  • Review events: kubectl get events"
    echo
    echo "⚡ AUTOMATION:"
    echo "  • Use this management suite daily"
    echo "  • Schedule health checks with cron"
    echo "  • Automate common maintenance tasks"
    echo "  • Document all manual interventions"
    echo
    read -p "Press Enter to return to menu..."
}

main_loop() {
    while true; do
        show_menu
        
        case $choice in
            1)
                if [ -f "$SCRIPT_DIR/dashboard.sh" ]; then
                    bash "$SCRIPT_DIR/dashboard.sh"
                else
                    echo "Dashboard script not found!"
                fi
                ;;
            2)
                if [ -f "$SCRIPT_DIR/health-check.sh" ]; then
                    bash "$SCRIPT_DIR/health-check.sh"
                else
                    echo "Health check script not found!"
                fi
                read -p "Press Enter to continue..."
                ;;
            3)
                echo -e "${YELLOW}🧹 Cleaning up failed resources...${NC}"
                kubectl delete pods --field-selector=status.phase=Failed -n $NAMESPACE --ignore-not-found=true
                echo -e "${GREEN}✅ Cleanup completed${NC}"
                read -p "Press Enter to continue..."
                ;;
            4)
                if [ -f "$SCRIPT_DIR/comprehensive-maintenance.sh" ]; then
                    bash "$SCRIPT_DIR/comprehensive-maintenance.sh" full
                else
                    echo "Maintenance script not found!"
                fi
                read -p "Press Enter to continue..."
                ;;
            5)
                echo "Enter deployment name:"
                read deployment
                echo "Enter new image:"
                read image
                if [ -f "$SCRIPT_DIR/deployment-management.sh" ]; then
                    bash "$SCRIPT_DIR/deployment-management.sh" update "$deployment" "$image"
                else
                    echo "Deployment management script not found!"
                fi
                read -p "Press Enter to continue..."
                ;;
            6)
                echo "Enter deployment name:"
                read deployment
                echo "Enter replica count:"
                read replicas
                if [ -f "$SCRIPT_DIR/deployment-management.sh" ]; then
                    bash "$SCRIPT_DIR/deployment-management.sh" scale "$deployment" "$replicas"
                else
                    echo "Deployment management script not found!"
                fi
                read -p "Press Enter to continue..."
                ;;
            7)
                echo "Enter service name:"
                read service
                if [ -f "$SCRIPT_DIR/deployment-management.sh" ]; then
                    bash "$SCRIPT_DIR/deployment-management.sh" circuit-breaker "$service"
                else
                    echo "Deployment management script not found!"
                fi
                read -p "Press Enter to continue..."
                ;;
            8)
                if [ -f "$SCRIPT_DIR/comprehensive-maintenance.sh" ]; then
                    bash "$SCRIPT_DIR/comprehensive-maintenance.sh" health-check
                else
                    echo "Maintenance script not found!"
                fi
                read -p "Press Enter to continue..."
                ;;
            9)
                if [ -f "$SCRIPT_DIR/comprehensive-maintenance.sh" ]; then
                    bash "$SCRIPT_DIR/comprehensive-maintenance.sh" data-flow
                else
                    echo "Maintenance script not found!"
                fi
                read -p "Press Enter to continue..."
                ;;
            10)
                if [ -f "$SCRIPT_DIR/comprehensive-maintenance.sh" ]; then
                    bash "$SCRIPT_DIR/comprehensive-maintenance.sh" alerts
                else
                    echo "Maintenance script not found!"
                fi
                read -p "Press Enter to continue..."
                ;;
            11)
                deploy_management_tools
                read -p "Press Enter to continue..."
                ;;
            12)
                show_best_practices
                ;;
            0)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${YELLOW}Invalid option. Please try again.${NC}"
                sleep 2
                ;;
        esac
    done
}

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null

echo -e "${GREEN}🚀 Crypto Service Management Suite${NC}"
echo "Loading..."
sleep 2

main_loop