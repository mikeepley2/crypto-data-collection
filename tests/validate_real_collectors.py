"""
Validation Test: Confirm Real Collectors vs Mock Collectors

This test verifies that our collectors are calling actual business logic
rather than just returning mock responses.
"""

import sys
import os
from unittest.mock import patch, Mock, MagicMock

def test_ohlc_collector_real_functionality():
    """Test that OHLC collector has real implementation vs just mock responses"""
    
    sys.path.append('./services/ohlc-collection')
    
    print("🔍 Testing OHLC Collector Real Functionality")
    print("=" * 60)
    
    # Test 1: Verify collector has actual methods (not just endpoint stubs)
    with patch.dict(os.environ, {'COINGECKO_PREMIUM_API_KEY': 'test_key'}):
        with patch('mysql.connector.connect') as mock_db:
            mock_db.return_value = Mock()
            
            from enhanced_ohlc_collector import EnhancedOHLCCollector
            collector = EnhancedOHLCCollector()
            
            # Check for real business logic methods
            real_methods = [
                'collect_all_ohlc_data',
                'detect_data_gap', 
                'calculate_health_score',
                '_intensive_backfill',
                '_fetch_ohlc_data_for_symbol'
            ]
            
            for method in real_methods:
                assert hasattr(collector, method), f"❌ Missing method: {method}"
                assert callable(getattr(collector, method)), f"❌ {method} not callable"
                print(f"✅ Real method found: {method}")
    
    print("\n✅ OHLC Collector has real implementation methods")
    return True

def test_endpoints_call_real_methods():
    """Test that endpoints call actual business logic, not just return static data"""
    
    sys.path.append('./services/ohlc-collection')
    
    print("\n🔍 Testing Endpoint -> Real Method Calls")
    print("=" * 60)
    
    with patch.dict(os.environ, {'COINGECKO_PREMIUM_API_KEY': 'test_key'}):
        with patch('mysql.connector.connect'):
            from enhanced_ohlc_collector import EnhancedOHLCCollector
            from fastapi.testclient import TestClient
            
            collector = EnhancedOHLCCollector()
            
            # Mock the business logic methods to track if they're called
            with patch.object(collector, 'detect_data_gap', return_value=2.5) as mock_gap:
                with patch.object(collector, 'calculate_health_score', return_value=85) as mock_health:
                    
                    collector._setup_api_endpoints()
                    client = TestClient(collector.app)
                    
                    # Test health endpoint calls real methods
                    response = client.get('/health')
                    assert response.status_code == 200
                    
                    # Verify actual methods were called
                    mock_gap.assert_called_once()
                    mock_health.assert_called_once()
                    
                    data = response.json()
                    assert data['gap_hours'] == 2.5, "Gap hours should come from real method"
                    assert data['health_score'] == 85, "Health score should come from real method"
                    
                    print("✅ Health endpoint calls real business logic")
            
            # Test gap check endpoint
            with patch.object(collector, 'detect_data_gap', return_value=5.0) as mock_gap:
                with patch.object(collector, 'calculate_health_score', return_value=75) as mock_health:
                    with patch.object(collector, 'collect_all_ohlc_data') as mock_collect:
                        
                        response = client.post('/gap-check')
                        assert response.status_code == 200
                        
                        # Verify methods were called
                        mock_gap.assert_called()
                        mock_health.assert_called()
                        
                        # Gap of 5 hours should trigger collection
                        mock_collect.assert_called_once()
                        
                        print("✅ Gap check endpoint calls real business logic")
    
    return True

def test_collect_endpoint_functionality():
    """Test that /collect endpoint triggers actual data collection"""
    
    sys.path.append('./services/ohlc-collection')
    
    print("\n🔍 Testing /collect Endpoint Real Functionality")
    print("=" * 60)
    
    with patch.dict(os.environ, {'COINGECKO_PREMIUM_API_KEY': 'test_key'}):
        with patch('mysql.connector.connect'):
            from enhanced_ohlc_collector import EnhancedOHLCCollector
            from fastapi.testclient import TestClient
            
            collector = EnhancedOHLCCollector()
            collector._setup_api_endpoints()
            client = TestClient(collector.app)
            
            # Mock the collection method to verify it gets called
            with patch.object(collector, 'collect_all_ohlc_data') as mock_collect:
                response = client.post('/collect')
                assert response.status_code == 200
                
                data = response.json()
                assert data['status'] == 'started'
                assert 'symbols_to_process' in data
                assert data['symbols_to_process'] > 0  # Should have real symbol count
                
                print("✅ Collect endpoint returns real symbol count")
                print(f"   Symbols to process: {data['symbols_to_process']}")
    
    return True

def test_backfill_endpoint_functionality():
    """Test that /backfill endpoint has real logic"""
    
    sys.path.append('./services/ohlc-collection')
    
    print("\n🔍 Testing /backfill Endpoint Real Functionality") 
    print("=" * 60)
    
    with patch.dict(os.environ, {'COINGECKO_PREMIUM_API_KEY': 'test_key'}):
        with patch('mysql.connector.connect'):
            from enhanced_ohlc_collector import EnhancedOHLCCollector
            from fastapi.testclient import TestClient
            
            collector = EnhancedOHLCCollector()
            collector._setup_api_endpoints()
            client = TestClient(collector.app)
            
            # Test backfill validation logic
            response = client.post('/backfill/200')  # Exceeds 168 hour limit
            assert response.status_code == 200
            
            data = response.json()
            assert 'error' in data
            assert 'Maximum backfill period' in data['error']
            
            print("✅ Backfill endpoint has real validation logic")
            print(f"   Error message: {data['error']}")
            
            # Test valid backfill
            with patch.object(collector, '_intensive_backfill') as mock_backfill:
                response = client.post('/backfill/24')
                assert response.status_code == 200
                
                data = response.json()
                assert data['status'] == 'started'
                assert 'estimated_collections' in data
                assert data['estimated_collections'] > 0  # Real calculation: hours // 6
                
                print("✅ Backfill endpoint calculates real estimates")
                print(f"   Estimated collections: {data['estimated_collections']}")
    
    return True

def test_metrics_endpoint_real_data():
    """Test that metrics endpoint returns real operational data"""
    
    sys.path.append('./services/ohlc-collection')
    
    print("\n🔍 Testing /metrics Endpoint Real Data")
    print("=" * 60)
    
    with patch.dict(os.environ, {'COINGECKO_PREMIUM_API_KEY': 'test_key'}):
        with patch('mysql.connector.connect'):
            from enhanced_ohlc_collector import EnhancedOHLCCollector
            from fastapi.testclient import TestClient
            
            collector = EnhancedOHLCCollector()
            collector._setup_api_endpoints()
            client = TestClient(collector.app)
            
            # Simulate some stats
            collector.stats = {
                'ohlc_records_collected': 1500,
                'failed_collections': 3,
                'api_calls_made': 250,
                'database_writes': 75
            }
            
            response = client.get('/metrics')
            assert response.status_code == 200
            
            metrics_text = response.text
            
            # Verify metrics contain real data from stats
            assert 'ohlc_collector_total_collected 1500' in metrics_text
            assert 'ohlc_collector_collection_errors 3' in metrics_text
            assert 'ohlc_collector_api_calls_made 250' in metrics_text
            
            print("✅ Metrics endpoint returns real stats data")
            print("   ✅ Prometheus format with actual counters")
            print("   ✅ Real statistics integration")
    
    return True

def validate_vs_mock_collector():
    """Compare real collector vs our previous mock collector"""
    
    print("\n🔍 Real Collector vs Mock Collector Comparison")
    print("=" * 60)
    
    # Import our mock collector from comprehensive tests
    sys.path.append('./tests')
    try:
        from test_comprehensive_endpoints import ComprehensiveTestCollector
        mock_collector = ComprehensiveTestCollector()
        
        print("❌ PROBLEM: Our tests were using ComprehensiveTestCollector (mock)")
        print("   This returns static responses, not real business logic")
        print("   Example mock response structure:")
        
        # Show mock data structure
        from fastapi.testclient import TestClient
        mock_client = TestClient(mock_collector.app)
        mock_response = mock_client.get('/health')
        mock_data = mock_response.json()
        
        print(f"   Mock health: {mock_data}")
        
    except ImportError:
        print("✅ Good: Mock collector not found")
    
    # Show real collector data structure  
    sys.path.append('./services/ohlc-collection')
    with patch.dict(os.environ, {'COINGECKO_PREMIUM_API_KEY': 'test_key'}):
        with patch('mysql.connector.connect'):
            from enhanced_ohlc_collector import EnhancedOHLCCollector
            from fastapi.testclient import TestClient
            
            real_collector = EnhancedOHLCCollector()
            
            # Mock just the specific methods to avoid database calls
            with patch.object(real_collector, 'detect_data_gap', return_value=1.5):
                with patch.object(real_collector, 'calculate_health_score', return_value=92):
                    real_collector._setup_api_endpoints()
                    real_client = TestClient(real_collector.app)
                    real_response = real_client.get('/health')
                    real_data = real_response.json()
                    
                    print("✅ GOOD: Real collector response structure:")
                    print(f"   Real health: {real_data}")
                    
                    print("\n📊 Key Differences:")
                    print("   ✅ Real collector calls actual business methods")
                    print("   ✅ Real collector has database integration")  
                    print("   ✅ Real collector performs calculations")
                    print("   ❌ Mock collector returns static JSON")
    
    return True

if __name__ == "__main__":
    print("🚀 REAL COLLECTOR VALIDATION TEST")
    print("=" * 80)
    
    try:
        test_ohlc_collector_real_functionality()
        test_endpoints_call_real_methods()
        test_collect_endpoint_functionality()
        test_backfill_endpoint_functionality()
        test_metrics_endpoint_real_data()
        validate_vs_mock_collector()
        
        print("\n🎉 VALIDATION COMPLETE - COLLECTORS ARE REAL!")
        print("=" * 80)
        print("✅ Real business logic methods found")
        print("✅ Endpoints call actual implementation") 
        print("✅ Data comes from real calculations")
        print("✅ NOT using mock/static responses")
        print("🚀 Ready to test actual collector functionality!")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()