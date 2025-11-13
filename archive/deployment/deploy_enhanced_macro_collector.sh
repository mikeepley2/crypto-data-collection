#!/bin/bash
"""
Enhanced Macro Collector Deployment Script
- Deploys the enhanced macro collector to Kubernetes
- Ensures continuous operation with gap prevention
- Sets up monitoring and health checks
"""

echo "🚀 DEPLOYING ENHANCED MACRO COLLECTOR"
echo "====================================="

echo ""
echo "📋 Deployment Overview:"
echo "• Enhanced gap detection and automatic backfilling"
echo "• Continuous collection every 2 hours"
echo "• Daily health checks at 06:00"
echo "• Automatic restart on failure"
echo "• Monitors all 11 key macro indicators"

echo ""
echo "🔍 Pre-deployment checks..."

# Check if namespace exists
if kubectl get namespace crypto-data-collection >/dev/null 2>&1; then
    echo "✅ Namespace crypto-data-collection exists"
else
    echo "❌ Namespace crypto-data-collection not found"
    echo "Creating namespace..."
    kubectl create namespace crypto-data-collection
fi

# Check if old macro collector is running
if kubectl get deployment macro-collector -n crypto-data-collection >/dev/null 2>&1; then
    echo "⚠️ Old macro-collector found - stopping..."
    kubectl scale deployment macro-collector --replicas=0 -n crypto-data-collection
    echo "✅ Old collector stopped"
fi

echo ""
echo "📁 Creating enhanced macro collector ConfigMap..."

# Create ConfigMap with the enhanced collector code
kubectl create configmap enhanced-macro-collector-code \
  --from-file=enhanced_macro_collector.py \
  --namespace=crypto-data-collection \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✅ ConfigMap created/updated"

echo ""
echo "🚀 Deploying enhanced macro collector..."

# Apply the deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-macro-collector
  namespace: crypto-data-collection
  labels:
    app: enhanced-macro-collector
    version: "2.0"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: enhanced-macro-collector
  template:
    metadata:
      labels:
        app: enhanced-macro-collector
        version: "2.0"
    spec:
      containers:
      - name: enhanced-macro-collector
        image: python:3.9-slim
        workingDir: /app
        command: ["/bin/bash"]
        args:
          - -c
          - |
            echo "🚀 Installing dependencies..."
            pip install mysql-connector-python requests schedule
            echo "✅ Dependencies installed"
            echo "🎯 Starting Enhanced Macro Collector..."
            python enhanced_macro_collector.py
        env:
        - name: DB_HOST
          value: "host.docker.internal"
        - name: DB_PORT
          value: "3306"
        - name: DB_USER
          value: "news_collector"
        - name: DB_PASSWORD
          value: "99Rules!"
        - name: DB_NAME
          value: "crypto_prices"
        - name: FRED_API_KEY
          value: "35478996c5e061d0fc99fc73f5ce348d"
        - name: TZ
          value: "UTC"
        volumeMounts:
        - name: collector-code
          mountPath: /app
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - /bin/bash
            - -c
            - |
              if [ -f /tmp/enhanced_macro_collector_health.txt ]; then
                last_update=\$(cat /tmp/enhanced_macro_collector_health.txt)
                current_time=\$(date -u +%s)
                last_time=\$(date -d "\$last_update" +%s 2>/dev/null || echo 0)
                diff=\$((current_time - last_time))
                if [ \$diff -lt 14400 ]; then  # 4 hours tolerance
                  exit 0
                else
                  echo "Health check failed: \$diff seconds since last update"
                  exit 1
                fi
              else
                echo "Health file not found"
                exit 1
              fi
          initialDelaySeconds: 600  # 10 minutes for initial startup
          periodSeconds: 1800       # Check every 30 minutes
          timeoutSeconds: 30
          failureThreshold: 2
        readinessProbe:
          exec:
            command:
            - /bin/bash
            - -c
            - |
              # Check if process is running and health file exists
              pgrep -f "enhanced_macro_collector.py" > /dev/null && \
              [ -f /tmp/enhanced_macro_collector_health.txt ]
          initialDelaySeconds: 60
          periodSeconds: 300
          timeoutSeconds: 10
      volumes:
      - name: collector-code
        configMap:
          name: enhanced-macro-collector-code
      restartPolicy: Always
---
apiVersion: v1
kind: Service
metadata:
  name: enhanced-macro-collector-service
  namespace: crypto-data-collection
  labels:
    app: enhanced-macro-collector
spec:
  selector:
    app: enhanced-macro-collector
  ports:
  - name: health
    port: 8080
    targetPort: 8080
  type: ClusterIP
EOF

echo "✅ Enhanced macro collector deployed"

echo ""
echo "⏰ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/enhanced-macro-collector -n crypto-data-collection

echo ""
echo "📊 Checking deployment status..."
kubectl get pods -n crypto-data-collection -l app=enhanced-macro-collector

echo ""
echo "📝 Deployment logs (last 20 lines):"
kubectl logs -n crypto-data-collection -l app=enhanced-macro-collector --tail=20

echo ""
echo "🎉 ENHANCED MACRO COLLECTOR DEPLOYMENT COMPLETE!"
echo "================================================"
echo ""
echo "🔍 Key Features Deployed:"
echo "✅ Automatic gap detection and backfilling on startup"
echo "✅ Continuous collection every 2 hours"
echo "✅ Daily health checks at 06:00 UTC"
echo "✅ Comprehensive coverage of all 11 indicators"
echo "✅ Robust error handling and retry logic"
echo "✅ Health monitoring and automatic restart"
echo ""
echo "📊 Monitoring Commands:"
echo "• Check status: kubectl get pods -n crypto-data-collection -l app=enhanced-macro-collector"
echo "• View logs: kubectl logs -n crypto-data-collection -l app=enhanced-macro-collector -f"
echo "• Health check: kubectl exec -n crypto-data-collection <pod-name> -- cat /tmp/enhanced_macro_collector_health.txt"
echo ""
echo "🎯 The enhanced collector will now:"
echo "1. Automatically detect and backfill any gaps on startup"
echo "2. Collect data every 2 hours to prevent future gaps"
echo "3. Run daily health checks to ensure all indicators are current"
echo "4. Restart automatically if any issues are detected"
echo ""
echo "🚀 Your macro indicators will now be continuously maintained with no gaps!"