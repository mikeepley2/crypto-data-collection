#!/usr/bin/env python3
"""
Continuous Collection System Monitor and Auto-Resolver
Real-time monitoring with automatic issue detection and resolution
"""

import asyncio
import subprocess
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import mysql.connector
from dataclasses import dataclass
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collection_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceStatus:
    name: str
    pod_status: str
    health_status: str
    last_collection: Optional[datetime]
    records_last_hour: int
    issues: List[str]
    auto_resolved: bool = False

@dataclass
class CollectionMetrics:
    timestamp: datetime
    service_name: str
    records_collected: int
    success_rate: float
    avg_response_time: float

class ContinuousCollectionMonitor:
    def __init__(self):
        self.running = True
        self.db_config = {
            'host': 'host.docker.internal',
            'user': 'news_collector', 
            'password': '99Rules!',
            'charset': 'utf8mb4'
        }
        
        # Service definitions with expected collection intervals (minutes)
        self.services = {
            'enhanced-crypto-prices': {'interval': 5, 'min_records_hour': 10, 'database': 'crypto_prices'},
            'crypto-news-collector': {'interval': 20, 'min_records_hour': 2, 'database': 'crypto_news'},
            'stock-news-collector': {'interval': 15, 'min_records_hour': 3, 'database': 'crypto_news'},
            'technical-indicators': {'interval': 10, 'min_records_hour': 5, 'database': 'crypto_prices'},
            'macro-economic': {'interval': 240, 'min_records_hour': 1, 'database': 'crypto_prices'},
            'social-other': {'interval': 30, 'min_records_hour': 1, 'database': 'crypto_news'},
            'onchain-data-collector': {'interval': 30, 'min_records_hour': 1, 'database': 'crypto_prices'},
            'crypto-sentiment-collector': {'interval': 15, 'min_records_hour': 2, 'database': 'crypto_news'},
            'stock-sentiment-collector': {'interval': 20, 'min_records_hour': 2, 'database': 'crypto_news'},
        }
        
        # Issue counters and resolution tracking
        self.issue_counts = {}
        self.last_restart_times = {}
        self.resolution_attempts = {}
        
        # Collector manager pod tracking
        self.collector_manager_pod = None
        
    def signal_handler(self, signum, frame):
        """Handle shutdown gracefully"""
        print(f"\n🛑 Received signal {signum}. Shutting down monitor...")
        self.running = False
        
    async def get_collector_manager_pod(self) -> Optional[str]:
        """Get current collector manager pod name"""
        try:
            result = subprocess.run([
                'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
                '-l', 'app=collector-manager', '--field-selector=status.phase=Running',
                '-o', 'jsonpath={.items[0].metadata.name}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get collector manager pod: {e}")
            return None
    
    def get_database_connection(self, database: str):
        """Get database connection for specified database"""
        config = self.db_config.copy()
        config['database'] = database
        return mysql.connector.connect(**config)
    
    def check_service_health(self, service_name: str) -> Dict:
        """Check if service is healthy via collector manager"""
        try:
            if not self.collector_manager_pod:
                return {'status': 'error', 'message': 'No collector manager pod'}
                
            result = subprocess.run([
                'kubectl', 'exec', '-it', self.collector_manager_pod,
                '-n', 'crypto-collectors', '--',
                'curl', '-s', '--max-time', '10',
                f'http://{service_name}.crypto-collectors.svc.cluster.local:8000/health'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and 'healthy' in result.stdout:
                return {'status': 'healthy', 'response': result.stdout}
            else:
                return {'status': 'unhealthy', 'message': result.stdout or result.stderr}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_pod_status(self, service_name: str) -> str:
        """Get Kubernetes pod status for service"""
        try:
            result = subprocess.run([
                'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
                '-l', f'app={service_name}', '--field-selector=status.phase=Running',
                '-o', 'jsonpath={.items[0].status.phase}'
            ], capture_output=True, text=True, timeout=10)
            
            return result.stdout.strip() or 'Not Found'
            
        except Exception as e:
            return f'Error: {e}'
    
    def get_recent_collection_data(self, service_name: str) -> Dict:
        """Get recent collection data for service"""
        try:
            database = self.services[service_name]['database']
            
            # Service-specific queries for recent data
            queries = {
                'enhanced-crypto-prices': """
                    SELECT COUNT(*) as count, MAX(timestamp) as latest
                    FROM crypto_prices 
                    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """,
                'crypto-news-collector': """
                    SELECT COUNT(*) as count, MAX(published_date) as latest
                    FROM crypto_news 
                    WHERE published_date >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """,
                'stock-news-collector': """
                    SELECT COUNT(*) as count, MAX(published_date) as latest
                    FROM stock_news 
                    WHERE published_date >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """,
                'technical-indicators': """
                    SELECT COUNT(*) as count, MAX(timestamp) as latest
                    FROM technical_indicators 
                    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """,
                'macro-economic': """
                    SELECT COUNT(*) as count, MAX(timestamp) as latest
                    FROM macro_indicators 
                    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """,
                'social-other': """
                    SELECT COUNT(*) as count, MAX(created_at) as latest
                    FROM reddit_posts 
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """,
                'onchain-data-collector': """
                    SELECT COUNT(*) as count, MAX(timestamp) as latest
                    FROM onchain_metrics 
                    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """,
                'crypto-sentiment-collector': """
                    SELECT COUNT(*) as count, MAX(timestamp) as latest
                    FROM crypto_sentiment_data 
                    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """,
                'stock-sentiment-collector': """
                    SELECT COUNT(*) as count, MAX(timestamp) as latest
                    FROM stock_sentiment_data 
                    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """
            }
            
            if service_name not in queries:
                return {'count': 0, 'latest': None, 'error': 'No query defined'}
                
            with self.get_database_connection(database) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(queries[service_name])
                result = cursor.fetchone()
                return result or {'count': 0, 'latest': None}
                
        except Exception as e:
            return {'count': 0, 'latest': None, 'error': str(e)}
    
    def trigger_collection(self, service_name: str) -> Dict:
        """Manually trigger collection for a service"""
        try:
            if not self.collector_manager_pod:
                return {'status': 'error', 'message': 'No collector manager pod'}
                
            result = subprocess.run([
                'kubectl', 'exec', '-it', self.collector_manager_pod,
                '-n', 'crypto-collectors', '--',
                'curl', '-s', '-X', 'POST',
                f'http://localhost:8000/services/{service_name}/collect',
                '-H', 'Content-Type: application/json', '-d', '{}'
            ], capture_output=True, text=True, timeout=60)
            
            if '"status":"success"' in result.stdout:
                return {'status': 'success', 'response': result.stdout}
            else:
                return {'status': 'failed', 'message': result.stdout or result.stderr}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a service deployment"""
        try:
            # Check if we've restarted this service recently
            now = datetime.now()
            if service_name in self.last_restart_times:
                last_restart = self.last_restart_times[service_name]
                if (now - last_restart).total_seconds() < 300:  # 5 minutes
                    logger.warning(f"⏳ Skipping restart of {service_name} - restarted recently")
                    return False
            
            logger.info(f"🔄 Restarting {service_name}...")
            
            result = subprocess.run([
                'kubectl', 'rollout', 'restart', f'deployment/{service_name}',
                '-n', 'crypto-collectors'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.last_restart_times[service_name] = now
                logger.info(f"✅ Successfully restarted {service_name}")
                return True
            else:
                logger.error(f"❌ Failed to restart {service_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error restarting {service_name}: {e}")
            return False
    
    def auto_resolve_issue(self, service_name: str, status: ServiceStatus) -> bool:
        """Automatically resolve common issues"""
        
        # Track resolution attempts
        if service_name not in self.resolution_attempts:
            self.resolution_attempts[service_name] = 0
            
        # Don't attempt too many auto-resolutions
        if self.resolution_attempts[service_name] >= 3:
            logger.warning(f"⚠️  Max auto-resolution attempts reached for {service_name}")
            return False
            
        self.resolution_attempts[service_name] += 1
        
        # Resolution strategies based on issues
        if 'Pod not running' in status.issues:
            logger.info(f"🔧 Auto-resolving: Restarting {service_name} (pod not running)")
            return self.restart_service(service_name)
            
        elif 'Health check failing' in status.issues:
            logger.info(f"🔧 Auto-resolving: Triggering collection for {service_name} (health failing)")
            result = self.trigger_collection(service_name)
            if result['status'] == 'success':
                return True
            else:
                # If trigger fails, try restart
                logger.info(f"🔧 Trigger failed, attempting restart for {service_name}")
                return self.restart_service(service_name)
                
        elif 'No recent data' in status.issues:
            logger.info(f"🔧 Auto-resolving: Triggering collection for {service_name} (no recent data)")
            result = self.trigger_collection(service_name)
            return result['status'] == 'success'
            
        return False
    
    def assess_service_status(self, service_name: str) -> ServiceStatus:
        """Comprehensive service status assessment"""
        
        # Get pod status
        pod_status = self.get_pod_status(service_name)
        
        # Get health status
        health_check = self.check_service_health(service_name)
        health_status = health_check['status']
        
        # Get recent collection data
        collection_data = self.get_recent_collection_data(service_name)
        records_last_hour = collection_data.get('count', 0)
        last_collection = collection_data.get('latest')
        
        # Identify issues
        issues = []
        
        if pod_status != 'Running':
            issues.append('Pod not running')
            
        if health_status != 'healthy':
            issues.append('Health check failing')
            
        min_expected = self.services[service_name]['min_records_hour']
        if records_last_hour < min_expected:
            issues.append('No recent data')
            
        # Check if data is stale
        if last_collection:
            if isinstance(last_collection, str):
                try:
                    last_collection = datetime.strptime(last_collection, '%Y-%m-%d %H:%M:%S')
                except:
                    last_collection = None
                    
            if last_collection:
                interval_minutes = self.services[service_name]['interval']
                expected_freshness = timedelta(minutes=interval_minutes * 2)  # 2x interval tolerance
                if datetime.now() - last_collection > expected_freshness:
                    issues.append('Data is stale')
        
        return ServiceStatus(
            name=service_name,
            pod_status=pod_status,
            health_status=health_status,
            last_collection=last_collection,
            records_last_hour=records_last_hour,
            issues=issues
        )
    
    def print_status_dashboard(self, service_statuses: List[ServiceStatus]):
        """Print real-time dashboard"""
        
        # Clear screen and print header
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("🚀 CRYPTO DATA COLLECTION - CONTINUOUS MONITOR")
        print("=" * 80)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 🔄 Auto-monitoring enabled")
        print("=" * 80)
        
        # Summary stats
        total_services = len(service_statuses)
        healthy_services = sum(1 for s in service_statuses if not s.issues)
        services_with_issues = sum(1 for s in service_statuses if s.issues and not s.auto_resolved)
        auto_resolved = sum(1 for s in service_statuses if s.auto_resolved)
        
        print(f"📊 STATUS: {healthy_services}/{total_services} Healthy | "
              f"⚠️  {services_with_issues} Issues | 🔧 {auto_resolved} Auto-resolved")
        print()
        
        # Service status table
        print("SERVICE                  | STATUS | HEALTH | RECORDS/1H | LAST COLLECTION     | ISSUES")
        print("-" * 90)
        
        for status in service_statuses:
            # Status indicators
            pod_icon = "✅" if status.pod_status == "Running" else "❌"
            health_icon = "✅" if status.health_status == "healthy" else "❌"
            data_icon = "✅" if status.records_last_hour > 0 else "⚠️"
            
            # Format last collection time
            if status.last_collection:
                if isinstance(status.last_collection, str):
                    last_coll = status.last_collection[:19]  # Truncate microseconds
                else:
                    last_coll = status.last_collection.strftime('%Y-%m-%d %H:%M:%S')
            else:
                last_coll = "Never"
                
            # Format issues
            issues_str = ", ".join(status.issues) if status.issues else "None"
            if status.auto_resolved:
                issues_str += " (Auto-resolved)"
                
            print(f"{status.name:<24} | {pod_icon:<6} | {health_icon:<6} | "
                  f"{data_icon} {status.records_last_hour:<7} | {last_coll:<19} | {issues_str}")
        
        print("-" * 90)
        print("💡 Press Ctrl+C to stop monitoring")
        print()
    
    async def monitor_cycle(self):
        """Single monitoring cycle"""
        
        # Update collector manager pod
        self.collector_manager_pod = await self.get_collector_manager_pod()
        
        if not self.collector_manager_pod:
            logger.error("❌ Cannot find running collector manager pod")
            return
        
        # Assess all services
        service_statuses = []
        
        for service_name in self.services.keys():
            status = self.assess_service_status(service_name)
            
            # Auto-resolve issues if possible
            if status.issues:
                # Track issue counts
                if service_name not in self.issue_counts:
                    self.issue_counts[service_name] = 0
                self.issue_counts[service_name] += 1
                
                # Attempt auto-resolution
                if self.auto_resolve_issue(service_name, status):
                    status.auto_resolved = True
                    logger.info(f"🔧 Auto-resolved issues for {service_name}")
                    
            else:
                # Reset issue count if service is healthy
                if service_name in self.issue_counts:
                    self.issue_counts[service_name] = 0
                    
            service_statuses.append(status)
        
        # Display dashboard
        self.print_status_dashboard(service_statuses)
        
        # Log critical issues
        critical_services = [s for s in service_statuses if s.issues and not s.auto_resolved]
        if critical_services:
            logger.warning(f"⚠️  {len(critical_services)} services have unresolved issues")
            for service in critical_services:
                logger.warning(f"   - {service.name}: {', '.join(service.issues)}")
    
    async def run_continuous_monitoring(self):
        """Main monitoring loop"""
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("🚀 Starting continuous collection monitoring...")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"🔄 Monitoring cycle {cycle_count}")
                
                await self.monitor_cycle()
                
                # Wait between cycles (30 seconds)
                for i in range(30):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring cycle: {e}")
                await asyncio.sleep(10)  # Wait before retrying
        
        logger.info("👋 Continuous monitoring stopped")

def main():
    """Main entry point"""
    monitor = ContinuousCollectionMonitor()
    
    print("🚀 CRYPTO DATA COLLECTION - CONTINUOUS MONITOR")
    print("=" * 60)
    print("🔍 Real-time service monitoring with auto-resolution")
    print("🔧 Automatically restarts failed services")
    print("📊 Tracks data collection rates and health")
    print("💡 Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        asyncio.run(monitor.run_continuous_monitoring())
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Monitor error: {e}")
        logger.error(f"Monitor error: {e}")

if __name__ == "__main__":
    main()