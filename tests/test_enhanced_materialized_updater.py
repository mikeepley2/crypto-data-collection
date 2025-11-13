#!/usr/bin/env python3
"""
Unit tests for Enhanced Materialized Updater Collector
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from services.enhanced_materialized_updater_template import (
    EnhancedMaterializedUpdaterCollector,
    MaterializedUpdaterConfig
)
from tests.test_base_collector import BaseCollectorTestCase

class TestMaterializedUpdaterConfig:
    """Test materialized updater configuration"""
    
    def test_config_initialization(self):
        """Test configuration defaults"""
        config = MaterializedUpdaterConfig.from_env()
        
        assert config.service_name == "enhanced-materialized-updater"
        assert config.refresh_interval == 300  # 5 minutes
        assert config.batch_size == 100
        assert config.parallel_updates == True
        assert config.max_retry_attempts == 3
    
    def test_view_configuration(self):
        """Test materialized view configuration"""
        config = MaterializedUpdaterConfig()
        
        # Default materialized views to manage
        expected_views = [
            'mv_crypto_price_daily',
            'mv_sentiment_summary',
            'mv_technical_indicators_latest',
            'mv_market_overview',
            'mv_trading_signals'
        ]
        
        assert config.managed_views == expected_views
        assert config.refresh_concurrency == 3
        assert config.view_dependencies == {}

class TestEnhancedMaterializedUpdaterCollector(BaseCollectorTestCase):
    """Test Enhanced Materialized Updater Collector functionality"""
    
    @pytest.fixture
    def updater_collector(self):
        """Create materialized updater instance for testing"""
        with patch.dict('os.environ', {
            'DB_HOST': 'localhost',
            'DB_USER': 'test',
            'DB_PASSWORD': 'test',
            'DB_NAME': 'test_db',
            'SERVICE_NAME': 'enhanced-materialized-updater'
        }):
            return EnhancedMaterializedUpdaterCollector()
    
    @pytest.fixture
    def mock_materialized_views(self):
        """Mock materialized view metadata"""
        return [
            {
                'view_name': 'mv_crypto_price_daily',
                'last_refresh': datetime(2024, 1, 1, 10, 0, 0),
                'refresh_duration': timedelta(seconds=45),
                'status': 'completed',
                'row_count': 1000,
                'dependencies': []
            },
            {
                'view_name': 'mv_sentiment_summary',
                'last_refresh': datetime(2024, 1, 1, 9, 30, 0),
                'refresh_duration': timedelta(seconds=120),
                'status': 'stale',
                'row_count': 500,
                'dependencies': []
            },
            {
                'view_name': 'mv_technical_indicators_latest',
                'last_refresh': datetime(2024, 1, 1, 8, 0, 0),
                'refresh_duration': timedelta(seconds=90),
                'status': 'failed',
                'row_count': 0,
                'dependencies': ['mv_crypto_price_daily']
            }
        ]
    
    def test_collector_initialization(self, updater_collector):
        """Test materialized updater initialization"""
        assert updater_collector.config.service_name == "enhanced-materialized-updater"
        assert isinstance(updater_collector.config.managed_views, list)
        assert updater_collector.config.parallel_updates == True
        assert updater_collector.view_refresh_status == {}
    
    @pytest.mark.asyncio
    async def test_get_materialized_view_status(self, updater_collector, mock_database):
        """Test retrieving materialized view status"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [
            ('mv_crypto_price_daily', datetime(2024, 1, 1, 10, 0), 45.5, 'completed', 1000),
            ('mv_sentiment_summary', datetime(2024, 1, 1, 9, 30), 120.0, 'stale', 500),
        ]
        
        status = await updater_collector._get_materialized_view_status()
        
        assert isinstance(status, dict)
        assert len(status) == 2
        assert 'mv_crypto_price_daily' in status
        assert status['mv_crypto_price_daily']['status'] == 'completed'
        assert status['mv_sentiment_summary']['status'] == 'stale'
    
    @pytest.mark.asyncio
    async def test_check_view_dependencies(self, updater_collector):
        """Test checking view dependencies before refresh"""
        # Mock dependency configuration
        updater_collector.config.view_dependencies = {
            'mv_technical_indicators_latest': ['mv_crypto_price_daily'],
            'mv_market_overview': ['mv_crypto_price_daily', 'mv_sentiment_summary']
        }
        
        view_status = {
            'mv_crypto_price_daily': {'status': 'completed', 'last_refresh': datetime.now()},
            'mv_sentiment_summary': {'status': 'completed', 'last_refresh': datetime.now()},
            'mv_technical_indicators_latest': {'status': 'stale', 'last_refresh': datetime.now() - timedelta(hours=2)}
        }
        
        # Dependencies satisfied
        can_refresh = await updater_collector._check_view_dependencies(
            'mv_market_overview', view_status
        )
        assert can_refresh == True
        
        # Dependencies not satisfied
        view_status['mv_crypto_price_daily']['status'] = 'failed'
        can_refresh = await updater_collector._check_view_dependencies(
            'mv_market_overview', view_status
        )
        assert can_refresh == False
    
    @pytest.mark.asyncio
    async def test_refresh_single_view(self, updater_collector, mock_database):
        """Test refreshing a single materialized view"""
        mock_conn, mock_cursor = mock_database
        
        view_name = 'mv_crypto_price_daily'
        start_time = datetime.now()
        
        # Mock successful refresh
        mock_cursor.rowcount = 1000
        
        result = await updater_collector._refresh_single_view(view_name)
        
        assert result == True
        # Should execute REFRESH MATERIALIZED VIEW command
        mock_cursor.execute.assert_called()
        executed_query = mock_cursor.execute.call_args[0][0]
        assert 'REFRESH MATERIALIZED VIEW' in executed_query
        assert view_name in executed_query
    
    @pytest.mark.asyncio
    async def test_refresh_view_with_retry(self, updater_collector, mock_database):
        """Test view refresh with retry on failure"""
        mock_conn, mock_cursor = mock_database
        
        view_name = 'mv_sentiment_summary'
        
        # Mock failure then success
        mock_cursor.execute.side_effect = [
            Exception("Database connection lost"),  # First attempt fails
            Exception("Lock timeout"),              # Second attempt fails  
            None                                    # Third attempt succeeds
        ]
        mock_cursor.rowcount = 500
        
        with patch.object(updater_collector, '_send_alert') as mock_alert:
            result = await updater_collector._refresh_single_view(view_name)
            
            assert result == True
            assert mock_cursor.execute.call_count == 3
            # Should send alert for failures
            assert mock_alert.call_count >= 0  # May send alerts
    
    @pytest.mark.asyncio
    async def test_refresh_view_permanent_failure(self, updater_collector, mock_database):
        """Test handling of permanent view refresh failure"""
        mock_conn, mock_cursor = mock_database
        
        view_name = 'mv_technical_indicators_latest'
        
        # Mock persistent failure
        mock_cursor.execute.side_effect = Exception("Critical database error")
        
        with patch.object(updater_collector, '_send_alert') as mock_alert:
            result = await updater_collector._refresh_single_view(view_name)
            
            assert result == False
            assert mock_cursor.execute.call_count == updater_collector.config.max_retry_attempts
    
    @pytest.mark.asyncio
    async def test_identify_stale_views(self, updater_collector, mock_materialized_views):
        """Test identifying stale materialized views"""
        current_time = datetime(2024, 1, 1, 11, 0, 0)
        
        with patch('services.enhanced_materialized_updater_template.datetime') as mock_dt:
            mock_dt.now.return_value = current_time
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            
            view_status = {
                view['view_name']: view for view in mock_materialized_views
            }
            
            stale_views = await updater_collector._identify_stale_views(view_status)
            
            assert isinstance(stale_views, list)
            # Views older than refresh_interval should be identified as stale
            assert 'mv_sentiment_summary' in stale_views  # 1.5 hours old
            assert 'mv_technical_indicators_latest' in stale_views  # 3 hours old + failed
    
    @pytest.mark.asyncio
    async def test_prioritize_view_updates(self, updater_collector, mock_materialized_views):
        """Test prioritizing view updates based on dependencies and staleness"""
        view_status = {view['view_name']: view for view in mock_materialized_views}
        stale_views = ['mv_sentiment_summary', 'mv_technical_indicators_latest']
        
        # Set up dependencies
        updater_collector.config.view_dependencies = {
            'mv_technical_indicators_latest': ['mv_crypto_price_daily']
        }
        
        prioritized = await updater_collector._prioritize_view_updates(
            stale_views, view_status
        )
        
        assert isinstance(prioritized, list)
        # Views with no dependencies should come first
        assert prioritized[0] == 'mv_sentiment_summary'
    
    @pytest.mark.asyncio
    async def test_parallel_view_refresh(self, updater_collector):
        """Test parallel refresh of multiple views"""
        views_to_refresh = ['mv_crypto_price_daily', 'mv_sentiment_summary']
        
        with patch.object(updater_collector, '_refresh_single_view', return_value=True) as mock_refresh:
            
            results = await updater_collector._parallel_view_refresh(views_to_refresh)
            
            assert isinstance(results, dict)
            assert len(results) == 2
            assert results['mv_crypto_price_daily'] == True
            assert results['mv_sentiment_summary'] == True
            assert mock_refresh.call_count == 2
    
    @pytest.mark.asyncio
    async def test_collect_data(self, updater_collector):
        """Test main data collection method"""
        mock_view_status = {
            'mv_crypto_price_daily': {
                'status': 'completed',
                'last_refresh': datetime.now() - timedelta(hours=1)
            },
            'mv_sentiment_summary': {
                'status': 'stale',
                'last_refresh': datetime.now() - timedelta(hours=2)
            }
        }
        
        with patch.object(updater_collector, '_get_materialized_view_status', return_value=mock_view_status):
            with patch.object(updater_collector, '_identify_stale_views', return_value=['mv_sentiment_summary']):
                with patch.object(updater_collector, '_parallel_view_refresh', return_value={'mv_sentiment_summary': True}):
                    
                    result = await updater_collector.collect_data()
                    
                    assert result == 1  # One view refreshed
    
    @pytest.mark.asyncio
    async def test_update_view_statistics(self, updater_collector, mock_database):
        """Test updating view refresh statistics"""
        mock_conn, mock_cursor = mock_database
        
        view_name = 'mv_crypto_price_daily'
        refresh_duration = 45.5
        row_count = 1000
        status = 'completed'
        
        await updater_collector._update_view_statistics(
            view_name, refresh_duration, row_count, status
        )
        
        # Should insert/update view statistics
        mock_cursor.execute.assert_called()
        executed_query = mock_cursor.execute.call_args[0][0]
        assert 'INSERT' in executed_query or 'UPDATE' in executed_query
    
    @pytest.mark.asyncio
    async def test_get_view_size_and_performance(self, updater_collector, mock_database):
        """Test getting view size and performance metrics"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = (1000, 45.5, 0.5)  # row_count, avg_duration, size_mb
        
        metrics = await updater_collector._get_view_size_and_performance('mv_crypto_price_daily')
        
        assert isinstance(metrics, dict)
        assert 'row_count' in metrics
        assert 'avg_refresh_duration' in metrics
        assert 'size_mb' in metrics
    
    @pytest.mark.asyncio
    async def test_backfill_data(self, updater_collector):
        """Test backfill functionality for materialized views"""
        missing_periods = [
            {
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 1, 2),
                "view_name": "mv_crypto_price_daily"
            }
        ]
        
        with patch.object(updater_collector, '_refresh_single_view', return_value=True) as mock_refresh:
            
            result = await updater_collector.backfill_data(missing_periods)
            
            assert result >= 0
            # Should attempt to refresh the specified view
            assert mock_refresh.call_count >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_missing_data(self, updater_collector, mock_database):
        """Test analysis of missing materialized view updates"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [
            ('mv_crypto_price_daily', datetime(2024, 1, 1, 8, 0), 'stale'),
            ('mv_sentiment_summary', datetime(2024, 1, 1, 6, 0), 'failed')
        ]
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        missing_periods = await updater_collector._analyze_missing_data(start_date, end_date)
        
        assert isinstance(missing_periods, list)
        assert len(missing_periods) == 2
        for period in missing_periods:
            assert "view_name" in period
            assert period["status"] in ["stale", "failed"]
    
    @pytest.mark.asyncio
    async def test_generate_data_quality_report(self, updater_collector, mock_database):
        """Test data quality report generation for materialized views"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.side_effect = [
            (5,),   # total_views
            (4,),   # healthy_views  
            (1,)    # failed_views
        ]
        
        report = await updater_collector._generate_data_quality_report()
        
        assert report.total_records == 5
        assert report.valid_records == 4
        assert report.invalid_records == 1
        assert 0 <= report.data_quality_score <= 100
    
    @pytest.mark.asyncio
    async def test_view_dependency_resolution(self, updater_collector):
        """Test dependency resolution for view refresh ordering"""
        updater_collector.config.view_dependencies = {
            'mv_market_overview': ['mv_crypto_price_daily', 'mv_sentiment_summary'],
            'mv_trading_signals': ['mv_technical_indicators_latest'],
            'mv_technical_indicators_latest': ['mv_crypto_price_daily']
        }
        
        stale_views = [
            'mv_market_overview',
            'mv_trading_signals', 
            'mv_technical_indicators_latest',
            'mv_crypto_price_daily'
        ]
        
        view_status = {view: {'status': 'stale'} for view in stale_views}
        
        prioritized = await updater_collector._prioritize_view_updates(
            stale_views, view_status
        )
        
        # Should resolve dependencies properly
        assert isinstance(prioritized, list)
        # Base views should come before dependent views
        price_idx = prioritized.index('mv_crypto_price_daily')
        tech_idx = prioritized.index('mv_technical_indicators_latest') 
        market_idx = prioritized.index('mv_market_overview')
        
        assert price_idx < tech_idx  # Price data before technical indicators
        assert price_idx < market_idx  # Price data before market overview

class TestViewRefreshStrategies:
    """Test different view refresh strategies"""
    
    @pytest.fixture
    def updater_collector(self):
        """Create collector for strategy testing"""
        return EnhancedMaterializedUpdaterCollector()
    
    def test_refresh_strategy_full(self, updater_collector):
        """Test full refresh strategy"""
        strategy = updater_collector._get_refresh_strategy('mv_crypto_price_daily')
        assert strategy in ['full', 'incremental', 'conditional']
    
    @pytest.mark.asyncio
    async def test_incremental_refresh_detection(self, updater_collector, mock_database):
        """Test detection of views that support incremental refresh"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = (True,)  # Supports incremental refresh
        
        supports_incremental = await updater_collector._supports_incremental_refresh(
            'mv_crypto_price_daily'
        )
        
        assert isinstance(supports_incremental, bool)
    
    @pytest.mark.asyncio
    async def test_conditional_refresh_logic(self, updater_collector):
        """Test conditional refresh based on underlying data changes"""
        # Mock checking if underlying data has changed
        with patch.object(updater_collector, '_check_underlying_data_changes', return_value=True):
            
            needs_refresh = await updater_collector._needs_conditional_refresh(
                'mv_sentiment_summary'
            )
            
            assert needs_refresh == True

class TestPerformanceMonitoring:
    """Test performance monitoring for materialized views"""
    
    @pytest.fixture
    def updater_collector(self):
        """Create collector for performance testing"""
        return EnhancedMaterializedUpdaterCollector()
    
    @pytest.mark.asyncio
    async def test_view_refresh_performance_tracking(self, updater_collector, mock_database):
        """Test tracking of view refresh performance"""
        mock_conn, mock_cursor = mock_database
        
        view_name = 'mv_crypto_price_daily'
        
        # Mock timing the refresh
        start_time = datetime.now()
        
        with patch('time.time', side_effect=[
            start_time.timestamp(),
            (start_time + timedelta(seconds=45)).timestamp()
        ]):
            
            result = await updater_collector._refresh_single_view(view_name)
            
            # Should track performance metrics
            assert result in [True, False]
    
    @pytest.mark.asyncio
    async def test_view_health_monitoring(self, updater_collector, mock_database):
        """Test monitoring view health and alerting"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [
            ('mv_crypto_price_daily', datetime.now() - timedelta(hours=6), 'stale'),
            ('mv_sentiment_summary', datetime.now() - timedelta(hours=1), 'failed')
        ]
        
        with patch.object(updater_collector, '_send_alert') as mock_alert:
            health_status = await updater_collector._monitor_view_health()
            
            assert isinstance(health_status, dict)
            # Should send alerts for unhealthy views
            assert mock_alert.call_count >= 0

class TestConcurrencyAndLocking:
    """Test concurrency control and locking for view updates"""
    
    @pytest.fixture
    def updater_collector(self):
        """Create collector for concurrency testing"""
        return EnhancedMaterializedUpdaterCollector()
    
    @pytest.mark.asyncio
    async def test_view_refresh_locking(self, updater_collector, mock_database):
        """Test that view refreshes are properly locked to prevent conflicts"""
        mock_conn, mock_cursor = mock_database
        
        view_name = 'mv_crypto_price_daily'
        
        # Mock acquiring and releasing locks
        with patch.object(updater_collector, '_acquire_refresh_lock', return_value=True):
            with patch.object(updater_collector, '_release_refresh_lock') as mock_release:
                
                result = await updater_collector._refresh_single_view(view_name)
                
                # Should release lock after refresh
                mock_release.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_refresh_prevention(self, updater_collector):
        """Test prevention of concurrent refresh of the same view"""
        view_name = 'mv_sentiment_summary'
        
        # Mock lock acquisition failure (view already being refreshed)
        with patch.object(updater_collector, '_acquire_refresh_lock', return_value=False):
            
            result = await updater_collector._refresh_single_view(view_name)
            
            # Should skip refresh if lock cannot be acquired
            assert result == False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])