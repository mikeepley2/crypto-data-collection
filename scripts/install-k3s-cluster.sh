#!/bin/bash
# K3s Multi-Server Installation Script
# This script sets up a production-ready K3s cluster across multiple servers

set -e

# Configuration variables
CLUSTER_NAME="crypto-production"
NODE_TOKEN_FILE="/var/lib/rancher/k3s/server/node-token"
K3S_CONFIG_FILE="/etc/rancher/k3s/config.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Install K3s server (master node)
install_k3s_server() {
    local server_ip=$1
    local is_primary=${2:-true}
    
    print_status "Installing K3s server on IP: $server_ip"
    
    # Create K3s config directory
    mkdir -p /etc/rancher/k3s
    
    # Create K3s config file
    cat > $K3S_CONFIG_FILE << EOF
# K3s Production Configuration
write-kubeconfig-mode: "0644"
cluster-cidr: "10.42.0.0/16"
service-cidr: "10.43.0.0/16"
cluster-dns: "10.43.0.10"
cluster-init: $is_primary
bind-address: "$server_ip"
advertise-address: "$server_ip"
node-ip: "$server_ip"
disable:
  - traefik  # We'll use nginx-ingress instead
flannel-backend: "vxlan"
EOF

    # Install K3s server
    if [ "$is_primary" = "true" ]; then
        print_status "Installing primary K3s server..."
        curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server --config=/etc/rancher/k3s/config.yaml" sh -
    else
        print_status "Installing secondary K3s server..."
        if [ -z "$K3S_TOKEN" ]; then
            print_error "K3S_TOKEN environment variable is required for secondary servers"
            exit 1
        fi
        curl -sfL https://get.k3s.io | K3S_TOKEN="$K3S_TOKEN" INSTALL_K3S_EXEC="server --config=/etc/rancher/k3s/config.yaml" sh -
    fi
    
    # Wait for K3s to be ready
    print_status "Waiting for K3s server to be ready..."
    while ! kubectl get nodes &>/dev/null; do
        sleep 5
    done
    
    print_status "K3s server installation complete!"
    
    # Display cluster info
    kubectl get nodes
    kubectl cluster-info
    
    # Save token for agent nodes
    if [ "$is_primary" = "true" ]; then
        print_status "Server node token (save this for agent nodes):"
        cat $NODE_TOKEN_FILE
    fi
}

# Install K3s agent (worker node)
install_k3s_agent() {
    local server_url=$1
    local node_ip=$2
    
    print_status "Installing K3s agent connecting to: $server_url"
    
    if [ -z "$K3S_TOKEN" ]; then
        print_error "K3S_TOKEN environment variable is required"
        exit 1
    fi
    
    # Install K3s agent
    curl -sfL https://get.k3s.io | K3S_URL="$server_url" K3S_TOKEN="$K3S_TOKEN" K3S_NODE_IP="$node_ip" sh -
    
    print_status "K3s agent installation complete!"
}

# Install essential cluster components
install_cluster_components() {
    print_status "Installing essential cluster components..."
    
    # Install nginx-ingress controller
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
    
    # Wait for nginx-ingress to be ready
    print_status "Waiting for nginx-ingress controller..."
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=300s
    
    # Install metrics-server
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    print_status "Cluster components installation complete!"
}

# Setup kubectl configuration for remote access
setup_kubectl_access() {
    local master_ip=$1
    
    print_status "Setting up kubectl access..."
    
    # Copy kubeconfig
    mkdir -p ~/.kube
    cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
    
    # Update server address in kubeconfig
    sed -i "s/127.0.0.1/$master_ip/g" ~/.kube/config
    
    print_status "Kubeconfig saved to ~/.kube/config"
    print_status "You can now use kubectl to manage your cluster"
}

# Main installation function
main() {
    check_root
    
    case "${1:-}" in
        "server-primary")
            if [ -z "${2:-}" ]; then
                print_error "Usage: $0 server-primary <server-ip>"
                exit 1
            fi
            install_k3s_server "$2" true
            install_cluster_components
            setup_kubectl_access "$2"
            ;;
        "server-secondary")
            if [ -z "${2:-}" ] || [ -z "${K3S_TOKEN:-}" ]; then
                print_error "Usage: K3S_TOKEN=<token> $0 server-secondary <server-ip>"
                exit 1
            fi
            install_k3s_server "$2" false
            ;;
        "agent")
            if [ -z "${2:-}" ] || [ -z "${3:-}" ] || [ -z "${K3S_TOKEN:-}" ]; then
                print_error "Usage: K3S_TOKEN=<token> $0 agent <server-url> <node-ip>"
                print_error "Example: K3S_TOKEN=xyz123 $0 agent https://192.168.1.10:6443 192.168.1.11"
                exit 1
            fi
            install_k3s_agent "$2" "$3"
            ;;
        *)
            echo "K3s Multi-Server Installation Script"
            echo ""
            echo "Usage:"
            echo "  Primary server:    $0 server-primary <server-ip>"
            echo "  Secondary server:  K3S_TOKEN=<token> $0 server-secondary <server-ip>"
            echo "  Agent node:        K3S_TOKEN=<token> $0 agent <server-url> <node-ip>"
            echo ""
            echo "Examples:"
            echo "  # Install primary server"
            echo "  sudo $0 server-primary 192.168.1.10"
            echo ""
            echo "  # Install secondary server"
            echo "  sudo K3S_TOKEN=xyz123 $0 server-secondary 192.168.1.11"
            echo ""
            echo "  # Install agent node"
            echo "  sudo K3S_TOKEN=xyz123 $0 agent https://192.168.1.10:6443 192.168.1.12"
            exit 1
            ;;
    esac
}

main "$@"