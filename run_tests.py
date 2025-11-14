#!/usr/bin/env python3
"""
Comprehensive Test Execution Script for Crypto Data Collection

Orchestrates Docker container setup, test execution, and result reporting.
"""

import subprocess
import sys
import time
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class CryptoTestRunner:
    """Comprehensive test runner for crypto data collection system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.docker_compose_file = self.project_root / "docker-compose.test.yml"
        self.test_results_dir = self.project_root / "test-results"
        self.test_results_dir.mkdir(exist_ok=True)
        
    def check_requirements(self) -> bool:
        """Check if all requirements are met for testing"""
        print("🔍 Checking test requirements...")
        
        # Check Docker
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Docker: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker not found or not running")
            return False
        
        # Check Docker Compose
        try:
            result = subprocess.run(["docker", "compose", "version"], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            print("❌ Docker Compose not available")
            return False
        
        # Check docker-compose.test.yml exists
        if not self.docker_compose_file.exists():
            print(f"❌ Missing {self.docker_compose_file}")
            return False
        print(f"✅ Test compose file: {self.docker_compose_file}")
        
        # API keys are hardcoded in test configuration
        api_keys = {
            'COINGECKO_API_KEY': 'CG-94NCcVD2euxaGTZe94bS2oYz',
            'FRED_API_KEY': '35478996c5e061d0fc99fc73f5ce348d',
            'GUARDIAN_API_KEY': 'test_guardian_key'
        }
        
        print("✅ API keys configured for real API testing:")
        print(f"   CoinGecko Premium: {api_keys['COINGECKO_API_KEY'][:8]}...")
        print(f"   FRED Economic Data: {api_keys['FRED_API_KEY'][:8]}...")
        print(f"   Guardian News: {api_keys['GUARDIAN_API_KEY'][:8]}...")
        
        return True
    
    def setup_test_environment(self) -> bool:
        """Set up Docker test environment"""
        print("\n🏗️  Setting up test environment...")
        
        # Clean up any existing test containers
        print("   Cleaning up existing containers...")
        subprocess.run([
            "docker", "compose", "-f", str(self.docker_compose_file), 
            "down", "-v", "--remove-orphans"
        ], capture_output=True)
        
        # Build and start services
        print("   Building test containers...")
        try:
            result = subprocess.run([
                "docker", "compose", "-f", str(self.docker_compose_file),
                "up", "-d", "--build"
            ], capture_output=True, text=True, check=True)
            
            print("✅ Test containers started successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start containers: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    def wait_for_services(self, timeout: int = 120) -> bool:
        """Wait for all services to be ready"""
        print("\n⏳ Waiting for services to be ready...")
        
        services = [
            ('MySQL', 'localhost:3307'),
            ('Redis', 'localhost:6380'),
            ('Price Collector', 'localhost:8001'),
            ('Macro Collector', 'localhost:8002')
        ]
        
        start_time = time.time()
        
        for service_name, endpoint in services:
            print(f"   Checking {service_name}...")
            
            while time.time() - start_time < timeout:
                try:
                    # Check if port is open
                    import socket
                    host, port = endpoint.split(':')
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex((host, int(port)))
                    sock.close()
                    
                    if result == 0:
                        print(f"   ✅ {service_name} ready")
                        break
                        
                except Exception:
                    pass
                
                time.sleep(2)
            else:
                print(f"   ❌ {service_name} not ready after {timeout}s")
                return False
        
        print("✅ All services ready")
        return True
    
    def run_tests(self, test_types: List[str] = None, parallel: bool = True) -> Dict[str, Any]:
        """Run the test suite"""
        print("\n🧪 Running comprehensive test suite...")
        
        if test_types is None:
            test_types = ['unit', 'integration', 'database']
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {}
        
        for test_type in test_types:
            print(f"\n   Running {test_type} tests...")
            
            # Determine test paths
            if test_type == 'unit':
                test_path = 'tests/ -m "unit or not integration"'
            elif test_type == 'integration':
                test_path = 'tests/integration/'
            elif test_type == 'database':
                test_path = 'tests/test_database_validation.py'
            else:
                test_path = f'tests/ -m {test_type}'
            
            # Build pytest command
            pytest_cmd = [
                "docker", "compose", "-f", str(self.docker_compose_file),
                "run", "--rm", "test-runner",
                "pytest", test_path,
                "-v", "--tb=short",
                f"--junitxml=/app/test-results/{test_type}_results_{timestamp}.xml",
                f"--cov=services",
                f"--cov-report=html:/app/test-results/{test_type}_coverage_{timestamp}",
                "--durations=10"
            ]
            
            if parallel and test_type != 'integration':  # Integration tests run sequentially
                pytest_cmd.extend(["-n", "auto"])
            
            # Run tests
            start_time = time.time()
            try:
                result = subprocess.run(pytest_cmd, capture_output=True, text=True, check=False)
                duration = time.time() - start_time
                
                results[test_type] = {
                    'success': result.returncode == 0,
                    'return_code': result.returncode,
                    'duration': duration,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
                if result.returncode == 0:
                    print(f"   ✅ {test_type} tests passed ({duration:.1f}s)")
                else:
                    print(f"   ❌ {test_type} tests failed ({duration:.1f}s)")
                    
            except Exception as e:
                results[test_type] = {
                    'success': False,
                    'error': str(e),
                    'duration': time.time() - start_time
                }
                print(f"   ❌ {test_type} tests error: {e}")
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# 📊 Crypto Data Collection Test Report

**Generated:** {timestamp}
**Project:** Crypto Data Collection System
**Test Framework:** Docker + pytest + Real API Integration

## 🎯 Test Summary

"""
        
        total_success = True
        total_duration = 0
        
        for test_type, result in results.items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            duration = result.get('duration', 0)
            total_duration += duration
            
            if not result['success']:
                total_success = False
            
            report += f"- **{test_type.title()} Tests:** {status} ({duration:.1f}s)\n"
        
        overall_status = "✅ ALL TESTS PASSED" if total_success else "❌ SOME TESTS FAILED"
        report += f"\n**Overall Status:** {overall_status}\n"
        report += f"**Total Duration:** {total_duration:.1f}s\n\n"
        
        # Detailed results
        report += "## 📋 Detailed Results\n\n"
        
        for test_type, result in results.items():
            report += f"### {test_type.title()} Tests\n\n"
            
            if result['success']:
                report += "✅ **Status:** PASSED\n\n"
            else:
                report += "❌ **Status:** FAILED\n\n"
                if 'error' in result:
                    report += f"**Error:** {result['error']}\n\n"
                if result.get('stderr'):
                    report += f"**Error Output:**\n```\n{result['stderr'][:1000]}\n```\n\n"
            
            if result.get('stdout'):
                # Extract key metrics from pytest output
                stdout = result['stdout']
                if 'passed' in stdout or 'failed' in stdout:
                    lines = stdout.split('\n')
                    summary_line = next((line for line in lines if 'passed' in line or 'failed' in line), '')
                    report += f"**Summary:** {summary_line}\n\n"
        
        # Test coverage section
        report += "## 📈 Test Coverage\n\n"
        report += "Coverage reports are available in the `test-results/` directory.\n\n"
        
        # Recommendations
        report += "## 🔧 Recommendations\n\n"
        
        if not total_success:
            report += "### Failed Tests\n"
            for test_type, result in results.items():
                if not result['success']:
                    report += f"- Review {test_type} test failures\n"
                    report += f"- Check error logs in test-results/{test_type}_results_*.xml\n"
            report += "\n"
        
        report += "### Next Steps\n"
        report += "- Review coverage reports for untested code paths\n"
        report += "- Consider adding performance benchmarks for slow operations\n"
        report += "- Validate real API rate limiting compliance\n"
        report += "- Monitor database performance metrics\n\n"
        
        return report
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        try:
            subprocess.run([
                "docker", "compose", "-f", str(self.docker_compose_file),
                "down", "-v", "--remove-orphans"
            ], capture_output=True, check=True)
            print("✅ Test environment cleaned up")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Cleanup may be incomplete: {e}")
    
    def run_comprehensive_tests(self, test_types: List[str] = None, 
                               cleanup_after: bool = True, 
                               generate_report: bool = True) -> bool:
        """Run the complete test suite with setup, execution, and reporting"""
        print("🚀 Starting comprehensive crypto data collection tests...\n")
        
        try:
            # Pre-flight checks
            if not self.check_requirements():
                return False
            
            # Setup environment
            if not self.setup_test_environment():
                return False
            
            # Wait for services
            if not self.wait_for_services():
                return False
            
            # Run tests
            results = self.run_tests(test_types)
            
            # Generate report
            if generate_report:
                report = self.generate_report(results)
                
                report_file = self.test_results_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(report_file, 'w') as f:
                    f.write(report)
                
                print(f"\n📊 Test report generated: {report_file}")
                print("\n" + "="*60)
                print(report[:1000] + "..." if len(report) > 1000 else report)
                print("="*60)
            
            # Determine overall success
            overall_success = all(result['success'] for result in results.values())
            
            if overall_success:
                print("\n🎉 All tests passed successfully!")
            else:
                print("\n⚠️  Some tests failed - check the detailed report above")
            
            return overall_success
            
        except KeyboardInterrupt:
            print("\n⏹️  Tests interrupted by user")
            return False
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
            return False
        finally:
            if cleanup_after:
                self.cleanup()


def main():
    parser = argparse.ArgumentParser(description='Run comprehensive crypto data collection tests')
    parser.add_argument('--test-types', nargs='+', 
                       choices=['unit', 'integration', 'database', 'performance'],
                       default=['unit', 'integration', 'database'],
                       help='Types of tests to run')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup after tests (useful for debugging)')
    parser.add_argument('--no-report', action='store_true',
                       help='Skip generating test report')
    
    args = parser.parse_args()
    
    runner = CryptoTestRunner()
    success = runner.run_comprehensive_tests(
        test_types=args.test_types,
        cleanup_after=not args.no_cleanup,
        generate_report=not args.no_report
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()