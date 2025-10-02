#!/usr/bin/env python3
"""
30-Minute OHLC Collector Monitoring
Real-time monitoring of unified-ohlc-collector to ensure continuous operation
"""

import subprocess
import mysql.connector
import time
import json
from datetime import datetime, timedelta

class OHLCCollectorMonitor:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '99Rules!',
            'database': 'crypto_prices',
            'charset': 'utf8mb4'
        }
        self.monitoring_duration = 30 * 60  # 30 minutes
        self.check_interval = 60  # Check every minute
        self.start_time = datetime.now()
        self.baseline_record_count = self.get_current_record_count()
        self.pod_name = self.get_current_pod_name()
        
    def get_current_record_count(self):
        """Get current total record count as baseline"""
        try:
            with mysql.connector.connect(**self.db_config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM ohlc_data")
                return cursor.fetchone()[0]
        except:
            return 0
    
    def get_current_pod_name(self):
        """Get the current pod name"""
        try:
            cmd = "kubectl get pods -n crypto-collectors -l app=unified-ohlc-collector -o json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                pods_data = json.loads(result.stdout)
                pods = pods_data.get('items', [])
                if pods:
                    return pods[0]['metadata']['name']
        except:
            pass
        return "unknown"
    
    def check_database_activity(self):
        """Check for new database records"""
        try:
            with mysql.connector.connect(**self.db_config) as conn:
                cursor = conn.cursor()
                
                # Current total
                cursor.execute("SELECT COUNT(*) FROM ohlc_data")
                current_total = cursor.fetchone()[0]
                
                # Records in last 5 minutes
                cursor.execute("""
                    SELECT COUNT(*) FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
                """)
                last_5min = cursor.fetchone()[0]
                
                # Records in last hour
                cursor.execute("""
                    SELECT COUNT(*) FROM ohlc_data 
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                """)
                last_hour = cursor.fetchone()[0]
                
                # Latest record
                cursor.execute("""
                    SELECT symbol, timestamp_iso 
                    FROM ohlc_data 
                    ORDER BY id DESC 
                    LIMIT 1
                """)
                latest = cursor.fetchone()
                
                return {
                    'total_records': current_total,
                    'new_records': current_total - self.baseline_record_count,
                    'last_5min': last_5min,
                    'last_hour': last_hour,
                    'latest_record': latest
                }
        except Exception as e:
            return {'error': str(e)}
    
    def check_pod_health(self):
        """Check pod health and logs"""
        try:
            # Check pod status
            cmd = f"kubectl get pod {self.pod_name} -n crypto-collectors -o json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            pod_healthy = False
            restart_count = 0
            
            if result.returncode == 0:
                pod_data = json.loads(result.stdout)
                status = pod_data.get('status', {})
                phase = status.get('phase', 'Unknown')
                
                containers = status.get('containerStatuses', [])
                if containers:
                    container = containers[0]
                    restart_count = container.get('restartCount', 0)
                    ready = container.get('ready', False)
                    pod_healthy = phase == 'Running' and ready
            
            # Get recent logs
            cmd = f"kubectl logs {self.pod_name} -n crypto-collectors --tail=5"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            recent_logs = []
            if result.returncode == 0:
                recent_logs = [line.strip() for line in result.stdout.split('\n') if line.strip()][-3:]
            
            return {
                'healthy': pod_healthy,
                'restart_count': restart_count,
                'recent_logs': recent_logs
            }
        except Exception as e:
            return {'error': str(e)}
    
    def print_status_update(self, check_number, db_status, pod_status):
        """Print formatted status update"""
        
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{int(elapsed.total_seconds() // 60):02d}:{int(elapsed.total_seconds() % 60):02d}"
        
        print(f"\n⏰ CHECK #{check_number} - {datetime.now().strftime('%H:%M:%S')} (Elapsed: {elapsed_str})")
        print("=" * 60)
        
        # Database status
        if 'error' in db_status:
            print(f"💾 DATABASE: ❌ Error - {db_status['error']}")
        else:
            total = db_status['total_records']
            new_records = db_status['new_records']
            last_5min = db_status['last_5min']
            last_hour = db_status['last_hour']
            
            print(f"💾 DATABASE:")
            print(f"   📊 Total Records: {total:,} (+{new_records} since start)")
            print(f"   🕐 Last 5 min: {last_5min} records")
            print(f"   📅 Last hour: {last_hour} records")
            
            if db_status['latest_record']:
                symbol, timestamp = db_status['latest_record']
                print(f"   🔄 Latest: {symbol} at {timestamp}")
            
            # Status indicators
            if new_records > 0:
                print("   🟢 Status: NEW DATA DETECTED!")
            elif last_5min > 0:
                print("   🟢 Status: RECENT ACTIVITY")
            elif last_hour > 0:
                print("   🟡 Status: Some recent activity")
            else:
                print("   🔴 Status: No recent activity")
        
        # Pod status
        if 'error' in pod_status:
            print(f"🔧 POD: ❌ Error - {pod_status['error']}")
        else:
            healthy = pod_status['healthy']
            restarts = pod_status['restart_count']
            
            print(f"🔧 POD:")
            print(f"   📦 Name: {self.pod_name}")
            print(f"   💚 Health: {'✅ HEALTHY' if healthy else '❌ UNHEALTHY'}")
            print(f"   🔄 Restarts: {restarts}")
            
            if pod_status['recent_logs']:
                print("   📝 Recent Activity:")
                for log in pod_status['recent_logs']:
                    print(f"     {log}")
    
    def run_monitoring(self):
        """Run the 30-minute monitoring session"""
        
        print("🎯 30-MINUTE OHLC COLLECTOR MONITORING")
        print("=" * 50)
        print(f"⏰ Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Baseline Records: {self.baseline_record_count:,}")
        print(f"📦 Monitoring Pod: {self.pod_name}")
        print(f"🔄 Check Interval: {self.check_interval} seconds")
        
        check_number = 0
        
        try:
            while True:
                check_number += 1
                
                # Perform checks
                db_status = self.check_database_activity()
                pod_status = self.check_pod_health()
                
                # Print status
                self.print_status_update(check_number, db_status, pod_status)
                
                # Check if monitoring period is complete
                elapsed = datetime.now() - self.start_time
                if elapsed.total_seconds() >= self.monitoring_duration:
                    break
                
                # Show countdown
                remaining = self.monitoring_duration - elapsed.total_seconds()
                remaining_str = f"{int(remaining // 60):02d}:{int(remaining % 60):02d}"
                print(f"⏳ Next check in {self.check_interval}s | Monitoring ends in {remaining_str}")
                
                # Wait for next check
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            print(f"\n\n⏹️  MONITORING STOPPED BY USER")
        
        # Final summary
        self.print_final_summary(check_number)
    
    def print_final_summary(self, total_checks):
        """Print final monitoring summary"""
        
        print(f"\n\n📋 FINAL MONITORING SUMMARY")
        print("=" * 40)
        
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        print(f"⏰ Start Time: {self.start_time.strftime('%H:%M:%S')}")
        print(f"⏰ End Time: {end_time.strftime('%H:%M:%S')}")
        print(f"⏱️  Duration: {int(total_duration.total_seconds() // 60)} minutes")
        print(f"🔍 Total Checks: {total_checks}")
        
        # Final database check
        final_db_status = self.check_database_activity()
        
        if 'error' not in final_db_status:
            final_count = final_db_status['total_records']
            total_new = final_count - self.baseline_record_count
            
            print(f"\n📊 DATABASE RESULTS:")
            print(f"   Starting Records: {self.baseline_record_count:,}")
            print(f"   Ending Records: {final_count:,}")
            print(f"   New Records Added: {total_new}")
            
            if total_new > 0:
                rate = total_new / (total_duration.total_seconds() / 3600)  # per hour
                print(f"   Collection Rate: {rate:.1f} records/hour")
                print(f"   🟢 RESULT: DATA COLLECTION ACTIVE ✅")
            else:
                print(f"   🔴 RESULT: NO NEW DATA COLLECTED ❌")
        
        # Final pod check
        final_pod_status = self.check_pod_health()
        
        if 'error' not in final_pod_status:
            if final_pod_status['healthy']:
                print(f"\n🔧 POD HEALTH: ✅ STABLE")
            else:
                print(f"\n🔧 POD HEALTH: ❌ ISSUES DETECTED")
        
        print(f"\n✨ MONITORING COMPLETE!")

if __name__ == "__main__":
    monitor = OHLCCollectorMonitor()
    monitor.run_monitoring()