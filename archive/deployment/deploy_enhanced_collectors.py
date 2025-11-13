#!/usr/bin/env python3
"""
Deploy and Test All Enhanced Collectors

This script provides a comprehensive deployment and testing framework for all enhanced collectors:
1. Technical Indicators Collector - Enhanced with dynamic symbols and backfill
2. Onchain Data Collector - New comprehensive blockchain metrics collection
3. News/Sentiment Collector - Enhanced with RSS feeds and crypto mention detection
4. Macro Indicators Collector - Enhanced with 16 FRED indicators and multi-frequency collection
5. Price Data Collector - Already running comprehensive backfill

Features:
- Health checks for all services
- Selective deployment testing
- Comprehensive backfill coordination
- Service status monitoring
"""

import os
import sys
import logging
import time
import subprocess
import requests
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import mysql.connector
from concurrent.futures import ThreadPoolExecutor, as_completed

def setup_logging():
    """Setup comprehensive logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('enhanced_collectors_deployment.log')
        ]
    )

class EnhancedCollectorDeployment:
    """Comprehensive deployment and testing framework"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.collectors = {
            "technical": {
                "name": "Technical Indicators Collector",
                "script": "execute_technical_backfill.py",
                "service_path": "services/technical-collection/enhanced_technical_calculator.py",
                "status": "unknown",
                "port": None,
                "health_url": None
            },
            "onchain": {
                "name": "Onchain Data Collector", 
                "script": "execute_onchain_backfill.py",
                "service_path": "services/onchain-collection/enhanced_onchain_collector.py",
                "status": "unknown",
                "port": None,
                "health_url": None
            },
            "news": {
                "name": "News/Sentiment Collector",
                "script": "execute_news_backfill.py",
                "service_path": "services/news-collection/enhanced_crypto_news_collector.py", 
                "status": "unknown",
                "port": 8001,
                "health_url": "http://localhost:8001/health"
            },
            "macro": {
                "name": "Macro Indicators Collector",
                "script": "execute_macro_backfill.py", 
                "service_path": "services/macro-collection/enhanced_macro_collector.py",
                "status": "unknown",
                "port": 8002,
                "health_url": "http://localhost:8002/health"
            },
            "price": {
                "name": "Price Data Collector",
                "script": "execute_comprehensive_price_backfill.py",
                "service_path": None,  # Already running
                "status": "running",
                "port": None,
                "health_url": None
            }
        }
        
        # Database configuration
        self.db_config = {
            "host": os.getenv("DB_HOST", "172.22.32.1"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "news_collector"),
            "password": os.getenv("DB_PASSWORD", "99Rules!"),
            "database": os.getenv("DB_NAME", "crypto_prices")
        }
        
    def get_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
            
    def check_collector_health(self, collector_key: str) -> Dict:
        """Check health of a specific collector"""
        collector = self.collectors[collector_key]
        
        try:
            # Check if service file exists
            if collector["service_path"] and not os.path.exists(collector["service_path"]):
                return {"status": "error", "message": "Service file not found"}
                
            # Check if test script exists
            if not os.path.exists(collector["script"]):
                return {"status": "error", "message": "Test script not found"}
                
            # For services with health URLs, check HTTP health
            if collector["health_url"]:
                try:
                    response = requests.get(collector["health_url"], timeout=5)
                    if response.status_code == 200:
                        return {"status": "healthy", "message": "Service responding"}
                    else:
                        return {"status": "unhealthy", "message": f"HTTP {response.status_code}"}
                except requests.exceptions.RequestException:
                    return {"status": "offline", "message": "Service not responding"}
                    
            # For non-HTTP services, check if processes are running or files are ready
            return {"status": "ready", "message": "Ready for deployment"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    def check_database_tables(self) -> Dict:
        """Check database table status"""
        table_status = {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check key tables
                tables_to_check = [
                    "price_data_real",
                    "technical_indicators", 
                    "onchain_data",
                    "crypto_news",
                    "macro_indicators",
                    "crypto_assets"
                ]
                
                for table in tables_to_check:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        
                        cursor.execute(f"SELECT MAX(created_at) FROM {table} WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
                        recent_data = cursor.fetchone()[0]
                        
                        table_status[table] = {
                            "total_records": count,
                            "recent_data": recent_data is not None,
                            "status": "healthy" if recent_data else ("populated" if count > 0 else "empty")
                        }
                        
                    except mysql.connector.Error as e:
                        table_status[table] = {
                            "error": str(e),
                            "status": "error"
                        }
                        
                return table_status
                
        except Exception as e:
            self.logger.error(f"Database check failed: {e}")
            return {"database_error": str(e)}
            
    def run_collector_test(self, collector_key: str) -> Dict:
        """Run test for a specific collector"""
        collector = self.collectors[collector_key]
        script_path = collector["script"]
        
        try:
            self.logger.info(f"🧪 Testing {collector['name']}...")
            
            # Run the test script
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "collector": collector_key,
                "name": collector["name"],
                "success": result.returncode == 0,
                "stdout": result.stdout[-1000:],  # Last 1000 chars
                "stderr": result.stderr[-1000:] if result.stderr else None,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "collector": collector_key,
                "name": collector["name"],
                "success": False,
                "error": "Test timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "collector": collector_key,
                "name": collector["name"],
                "success": False,
                "error": str(e)
            }
            
    def run_all_health_checks(self) -> Dict:
        """Run health checks for all collectors"""
        self.logger.info("🔍 Running comprehensive health checks...")
        
        health_results = {}
        
        # Check each collector
        for key, collector in self.collectors.items():
            self.logger.info(f"   Checking {collector['name']}...")
            health_results[key] = self.check_collector_health(key)
            
        # Check database
        self.logger.info("   Checking database tables...")
        health_results["database"] = self.check_database_tables()
        
        return health_results
        
    def run_selected_tests(self, collectors: List[str]) -> Dict:
        """Run tests for selected collectors"""
        self.logger.info(f"🧪 Running tests for: {', '.join(collectors)}")
        
        test_results = {}
        
        for collector_key in collectors:
            if collector_key in self.collectors:
                result = self.run_collector_test(collector_key)
                test_results[collector_key] = result
                
                if result["success"]:
                    self.logger.info(f"   ✅ {result['name']} test passed")
                else:
                    self.logger.error(f"   ❌ {result['name']} test failed")
                    
        return test_results
        
    def run_parallel_tests(self, collectors: List[str]) -> Dict:
        """Run tests in parallel for faster execution"""
        self.logger.info(f"🚀 Running parallel tests for: {', '.join(collectors)}")
        
        test_results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all test tasks
            future_to_collector = {
                executor.submit(self.run_collector_test, collector_key): collector_key
                for collector_key in collectors
                if collector_key in self.collectors
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_collector):
                collector_key = future_to_collector[future]
                try:
                    result = future.result()
                    test_results[collector_key] = result
                    
                    if result["success"]:
                        self.logger.info(f"   ✅ {result['name']} test completed successfully")
                    else:
                        self.logger.error(f"   ❌ {result['name']} test failed")
                        
                except Exception as e:
                    test_results[collector_key] = {
                        "collector": collector_key,
                        "success": False,
                        "error": f"Test execution failed: {e}"
                    }
                    
        return test_results
        
    def generate_deployment_report(self, health_results: Dict, test_results: Dict = None) -> str:
        """Generate comprehensive deployment report"""
        report_lines = []
        report_lines.append("📊 Enhanced Collectors Deployment Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append("")
        
        # Health Check Results
        report_lines.append("🔍 Health Check Results:")
        report_lines.append("-" * 25)
        
        for key, result in health_results.items():
            if key == "database":
                report_lines.append(f"\n📊 Database Status:")
                if isinstance(result, dict) and "database_error" not in result:
                    for table, info in result.items():
                        status_icon = "✅" if info["status"] == "healthy" else ("⚠️" if info["status"] == "populated" else "❌")
                        report_lines.append(f"   {status_icon} {table}: {info.get('total_records', 0)} records")
                else:
                    report_lines.append(f"   ❌ Database error: {result.get('database_error', 'Unknown')}")
            else:
                collector = self.collectors[key]
                status_icon = "✅" if result["status"] in ["healthy", "ready"] else "❌"
                report_lines.append(f"   {status_icon} {collector['name']}: {result['message']}")
                
        # Test Results
        if test_results:
            report_lines.append(f"\n🧪 Test Results:")
            report_lines.append("-" * 15)
            
            for key, result in test_results.items():
                collector = self.collectors[key]
                status_icon = "✅" if result["success"] else "❌"
                report_lines.append(f"   {status_icon} {collector['name']}: {'PASSED' if result['success'] else 'FAILED'}")
                
                if not result["success"] and "error" in result:
                    report_lines.append(f"      Error: {result['error']}")
                    
        # Recommendations
        report_lines.append(f"\n💡 Recommendations:")
        report_lines.append("-" * 17)
        
        healthy_count = sum(1 for k, v in health_results.items() 
                          if k != "database" and v["status"] in ["healthy", "ready"])
        total_collectors = len(self.collectors)
        
        if healthy_count == total_collectors:
            report_lines.append("   ✅ All collectors are ready for deployment")
            report_lines.append("   🚀 Recommend proceeding with comprehensive backfill")
        else:
            report_lines.append(f"   ⚠️  {total_collectors - healthy_count} collectors need attention")
            report_lines.append("   🔧 Address health issues before full deployment")
            
        return "\n".join(report_lines)

def interactive_deployment():
    """Interactive deployment workflow"""
    deployment = EnhancedCollectorDeployment()
    logger = logging.getLogger(__name__)
    
    print("🚀 Enhanced Collectors Deployment Framework")
    print("=" * 50)
    
    while True:
        print("\n🤔 Deployment Options:")
        print("1. Run health checks only")
        print("2. Test specific collectors")
        print("3. Test all collectors (sequential)")
        print("4. Test all collectors (parallel)")
        print("5. Generate deployment report")
        print("6. Exit")
        
        try:
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                print("\n🔍 Running health checks...")
                health_results = deployment.run_all_health_checks()
                
                print("\n📊 Health Check Summary:")
                for key, result in health_results.items():
                    if key == "database":
                        print(f"   📊 Database: {'✅ Healthy' if 'database_error' not in result else '❌ Error'}")
                    else:
                        collector = deployment.collectors[key]
                        status_icon = "✅" if result["status"] in ["healthy", "ready"] else "❌"
                        print(f"   {status_icon} {collector['name']}: {result['message']}")
                        
            elif choice == "2":
                print("\n📋 Available Collectors:")
                for i, (key, collector) in enumerate(deployment.collectors.items(), 1):
                    print(f"   {i}. {collector['name']} ({key})")
                    
                selection = input("\nEnter collector numbers (comma-separated): ").strip()
                
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(",")]
                    collector_keys = [list(deployment.collectors.keys())[i] for i in indices if 0 <= i < len(deployment.collectors)]
                    
                    if collector_keys:
                        test_results = deployment.run_selected_tests(collector_keys)
                        
                        print(f"\n📊 Test Summary:")
                        for key, result in test_results.items():
                            status = "✅ PASSED" if result["success"] else "❌ FAILED"
                            print(f"   {status} {result['name']}")
                    else:
                        print("❌ No valid collectors selected")
                        
                except ValueError:
                    print("❌ Invalid selection format")
                    
            elif choice == "3":
                print("\n🧪 Testing all collectors sequentially...")
                collector_keys = list(deployment.collectors.keys())
                test_results = deployment.run_selected_tests(collector_keys)
                
                print(f"\n📊 Complete Test Summary:")
                passed = sum(1 for r in test_results.values() if r["success"])
                total = len(test_results)
                print(f"   Results: {passed}/{total} tests passed")
                
                for key, result in test_results.items():
                    status = "✅ PASSED" if result["success"] else "❌ FAILED"
                    print(f"   {status} {result['name']}")
                    
            elif choice == "4":
                print("\n🚀 Testing all collectors in parallel...")
                collector_keys = list(deployment.collectors.keys())
                test_results = deployment.run_parallel_tests(collector_keys)
                
                print(f"\n📊 Parallel Test Summary:")
                passed = sum(1 for r in test_results.values() if r["success"])
                total = len(test_results)
                print(f"   Results: {passed}/{total} tests passed")
                
                for key, result in test_results.items():
                    status = "✅ PASSED" if result["success"] else "❌ FAILED"
                    print(f"   {status} {result['name']}")
                    
            elif choice == "5":
                print("\n📊 Generating comprehensive deployment report...")
                
                health_results = deployment.run_all_health_checks()
                
                # Ask if user wants to include test results
                run_tests = input("Include test results in report? (y/N): ").lower().strip() == 'y'
                test_results = None
                
                if run_tests:
                    print("   🧪 Running tests for report...")
                    collector_keys = list(deployment.collectors.keys())
                    test_results = deployment.run_parallel_tests(collector_keys)
                    
                report = deployment.generate_deployment_report(health_results, test_results)
                
                # Save report to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = f"deployment_report_{timestamp}.txt"
                
                with open(report_file, "w") as f:
                    f.write(report)
                    
                print(f"\n📄 Report saved to: {report_file}")
                print("\n" + report)
                
            elif choice == "6":
                print("\n👋 Exiting deployment framework")
                break
                
            else:
                print("❌ Invalid option. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled by user")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            print(f"❌ An error occurred: {e}")

def main():
    """Main execution function"""
    setup_logging()
    
    try:
        interactive_deployment()
    except Exception as e:
        print(f"❌ Deployment framework failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())