#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Enhanced Placeholder Manager

Tests the placeholder manager with real database operations and cross-service coordination.
"""

import pytest
import requests
import mysql.connector
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import time
import json


@pytest.mark.integration
@pytest.mark.database
class TestEnhancedPlaceholderManagerIntegration:
    """Integration tests for placeholder manager with real database operations"""
    
    def test_manager_health_endpoint(self):
        """Test placeholder manager health endpoint"""
        # Placeholder manager typically runs on port 8009
        response = requests.get("http://localhost:8009/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data
        assert 'managed_tables' in health_data
    
    def test_manager_readiness_endpoint(self):
        """Test placeholder manager readiness endpoint"""
        response = requests.get("http://localhost:8009/ready")
        assert response.status_code == 200
        
        ready_data = response.json()
        assert ready_data['ready'] is True
        assert 'database_connected' in ready_data
        assert 'collectors_status' in ready_data
    
    def test_create_placeholder_records(self, test_mysql_connection, test_symbols):
        """Test creating placeholder records for missing data"""
        response = requests.post(
            "http://localhost:8009/api/v1/placeholders/create",
            json={
                "table": "price_data_real",
                "symbols": test_symbols['primary'],
                "time_range": {
                    "start": (datetime.now() - timedelta(hours=24)).isoformat(),
                    "end": datetime.now().isoformat()
                },
                "interval": "1h"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'placeholders_created' in result
        assert 'affected_symbols' in result
        
        # Verify placeholders were created in database
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM price_data_real WHERE data_completeness_percentage = 0.0 ORDER BY created_at DESC LIMIT 10"
        )
        placeholders = cursor.fetchall()
        
        assert len(placeholders) > 0
        for placeholder in placeholders:
            assert placeholder['data_completeness_percentage'] == 0.0
            assert placeholder['symbol'] in test_symbols['primary']
        
        cursor.close()
    
    def test_identify_missing_data_gaps(self, test_mysql_connection):
        """Test identification of missing data gaps across all tables"""
        response = requests.post(
            "http://localhost:8009/api/v1/gaps/identify",
            json={
                "tables": ["price_data_real", "technical_indicators", "ohlc_data"],
                "symbols": ["bitcoin", "ethereum"],
                "time_window": "7d",
                "expected_frequency": {
                    "price_data_real": "5m",
                    "technical_indicators": "1h", 
                    "ohlc_data": "1h"
                }
            }
        )
        
        assert response.status_code == 200
        gaps = response.json()
        
        assert 'identified_gaps' in gaps
        assert 'gap_summary' in gaps
        assert 'priority_gaps' in gaps
        
        # Validate gap structure
        gap_summary = gaps['gap_summary']
        assert 'total_gaps' in gap_summary
        assert 'gaps_by_table' in gap_summary
        assert 'gaps_by_symbol' in gap_summary
        
        # Check gaps by table structure
        gaps_by_table = gap_summary['gaps_by_table']
        for table in ["price_data_real", "technical_indicators", "ohlc_data"]:
            if table in gaps_by_table:
                table_gaps = gaps_by_table[table]
                assert 'gap_count' in table_gaps
                assert 'total_missing_hours' in table_gaps
    
    def test_backfill_coordination(self, test_api_keys):
        """Test coordination of backfill operations across collectors"""
        response = requests.post(
            "http://localhost:8009/api/v1/backfill/coordinate",
            json={
                "operation_id": f"test_backfill_{int(time.time())}",
                "target_tables": ["price_data_real", "technical_indicators"],
                "symbols": ["bitcoin", "ethereum"],
                "time_range": {
                    "start": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "end": datetime.now().isoformat()
                },
                "priority": "high",
                "collectors": ["price", "technical"]
            },
            headers={"X-Operation-Key": "test_key"}
        )
        
        assert response.status_code == 200
        coordination = response.json()
        
        assert 'operation_id' in coordination
        assert 'scheduled_tasks' in coordination
        assert 'estimated_completion' in coordination
        assert 'collector_assignments' in coordination
        
        # Validate collector assignments
        assignments = coordination['collector_assignments']
        for collector in ['price', 'technical']:
            if collector in assignments:
                assignment = assignments[collector]
                assert 'assigned_symbols' in assignment
                assert 'priority' in assignment
                assert 'estimated_duration' in assignment
    
    def test_cross_table_consistency_check(self, test_mysql_connection):
        """Test cross-table data consistency validation"""
        response = requests.post(
            "http://localhost:8009/api/v1/consistency/check",
            json={
                "primary_table": "price_data_real",
                "related_tables": ["technical_indicators", "ohlc_data"],
                "symbols": ["bitcoin", "ethereum"],
                "consistency_rules": {
                    "timestamp_alignment": True,
                    "symbol_coverage": True,
                    "data_completeness_correlation": True
                }
            }
        )
        
        assert response.status_code == 200
        consistency = response.json()
        
        assert 'consistency_report' in consistency
        assert 'issues_found' in consistency
        assert 'recommendations' in consistency
        
        # Validate consistency report structure
        report = consistency['consistency_report']
        assert 'timestamp_alignment_score' in report
        assert 'symbol_coverage_score' in report
        assert 'overall_consistency_score' in report
        
        # Validate score ranges
        for score_key in ['timestamp_alignment_score', 'symbol_coverage_score', 'overall_consistency_score']:
            if score_key in report and report[score_key] is not None:
                assert 0 <= report[score_key] <= 100
    
    def test_data_quality_monitoring(self, test_mysql_connection):
        """Test data quality monitoring across all managed tables"""
        response = requests.get(
            "http://localhost:8009/api/v1/quality/monitor",
            params={
                "time_window": "24h",
                "include_trends": "true",
                "quality_thresholds": json.dumps({
                    "completeness_min": 85.0,
                    "freshness_max_age_hours": 2,
                    "consistency_min": 90.0
                })
            }
        )
        
        assert response.status_code == 200
        quality = response.json()
        
        assert 'quality_summary' in quality
        assert 'table_quality_scores' in quality
        assert 'quality_trends' in quality
        assert 'alerts' in quality
        
        # Validate quality summary
        summary = quality['quality_summary']
        assert 'overall_completeness' in summary
        assert 'data_freshness_score' in summary
        assert 'consistency_score' in summary
        
        # Check table-specific quality scores
        table_scores = quality['table_quality_scores']
        expected_tables = ['price_data_real', 'technical_indicators', 'ohlc_data', 'macro_indicators']
        
        for table in expected_tables:
            if table in table_scores:
                table_quality = table_scores[table]
                assert 'completeness_percentage' in table_quality
                assert 'record_count' in table_quality
                assert 'last_update' in table_quality
    
    def test_symbol_management(self, test_mysql_connection):
        """Test centralized symbol management functionality"""
        response = requests.post(
            "http://localhost:8009/api/v1/symbols/manage",
            json={
                "operation": "sync_all_tables",
                "add_missing_symbols": True,
                "remove_inactive_symbols": False,
                "symbol_sources": ["coingecko", "manual"]
            }
        )
        
        assert response.status_code == 200
        symbol_management = response.json()
        
        assert 'sync_summary' in symbol_management
        assert 'symbols_added' in symbol_management
        assert 'symbols_updated' in symbol_management
        
        # Validate sync summary
        sync_summary = symbol_management['sync_summary']
        assert 'tables_processed' in sync_summary
        assert 'total_symbols_managed' in sync_summary
        
        # Verify crypto_assets table was updated
        cursor = test_mysql_connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM crypto_assets WHERE is_active = 1")
        active_symbols = cursor.fetchone()
        
        assert active_symbols['count'] > 0
        cursor.close()
    
    def test_automated_cleanup_operations(self, test_mysql_connection):
        """Test automated cleanup of old placeholder and invalid data"""
        response = requests.post(
            "http://localhost:8009/api/v1/cleanup/automated",
            json={
                "cleanup_rules": {
                    "remove_old_placeholders": True,
                    "placeholder_max_age_hours": 168,  # 1 week
                    "remove_duplicate_records": True,
                    "cleanup_invalid_data": True
                },
                "tables": ["price_data_real", "technical_indicators"],
                "dry_run": False
            }
        )
        
        assert response.status_code == 200
        cleanup = response.json()
        
        assert 'cleanup_summary' in cleanup
        assert 'records_removed' in cleanup
        assert 'space_freed_mb' in cleanup
        
        # Validate cleanup summary
        summary = cleanup['cleanup_summary']
        assert 'tables_cleaned' in summary
        assert 'total_operations' in summary
        assert 'completion_time' in summary
    
    def test_collector_health_aggregation(self):
        """Test aggregation of health status from all collectors"""
        response = requests.get(
            "http://localhost:8009/api/v1/collectors/health_aggregate"
        )
        
        assert response.status_code == 200
        health_aggregate = response.json()
        
        assert 'overall_health' in health_aggregate
        assert 'collector_status' in health_aggregate
        assert 'system_metrics' in health_aggregate
        
        # Validate overall health status
        overall_health = health_aggregate['overall_health']
        assert overall_health in ['healthy', 'degraded', 'unhealthy']
        
        # Check individual collector status
        collector_status = health_aggregate['collector_status']
        expected_collectors = ['price', 'onchain', 'macro', 'news', 'technical']
        
        for collector in expected_collectors:
            if collector in collector_status:
                status = collector_status[collector]
                assert 'status' in status
                assert 'last_seen' in status
                assert 'response_time_ms' in status
    
    def test_performance_metrics_aggregation(self):
        """Test performance metrics aggregation across all collectors"""
        response = requests.get(
            "http://localhost:8009/api/v1/metrics/performance",
            params={"time_window": "1h"}
        )
        
        assert response.status_code == 200
        metrics = response.json()
        
        assert 'aggregated_metrics' in metrics
        assert 'collector_performance' in metrics
        assert 'database_performance' in metrics
        
        # Validate aggregated metrics
        aggregated = metrics['aggregated_metrics']
        assert 'total_records_processed' in aggregated
        assert 'average_processing_time' in aggregated
        assert 'error_rate_percentage' in aggregated
        
        # Validate error rate
        error_rate = aggregated['error_rate_percentage']
        assert 0 <= error_rate <= 100
    
    def test_emergency_data_recovery(self, test_api_keys, test_mysql_connection):
        """Test emergency data recovery coordination"""
        response = requests.post(
            "http://localhost:8009/api/v1/recovery/emergency",
            json={
                "recovery_scenario": "collector_outage",
                "affected_collector": "price",
                "affected_symbols": ["bitcoin", "ethereum"],
                "outage_duration_hours": 2,
                "recovery_priority": "critical",
                "use_backup_sources": True
            },
            headers={"X-Emergency-Key": "emergency_recovery_key"}
        )
        
        assert response.status_code == 200
        recovery = response.json()
        
        assert 'recovery_plan' in recovery
        assert 'estimated_recovery_time' in recovery
        assert 'backup_sources_activated' in recovery
        assert 'priority_queue_created' in recovery
        
        # Validate recovery plan
        plan = recovery['recovery_plan']
        assert 'steps' in plan
        assert 'resources_required' in plan
        assert 'success_criteria' in plan
    
    def test_data_completeness_global_view(self, test_mysql_connection):
        """Test global view of data completeness across all tables"""
        response = requests.get(
            "http://localhost:8009/api/v1/completeness/global_view",
            params={
                "symbols": "bitcoin,ethereum,solana",
                "time_range": "24h"
            }
        )
        
        assert response.status_code == 200
        completeness = response.json()
        
        assert 'global_completeness_score' in completeness
        assert 'table_completeness' in completeness
        assert 'symbol_completeness' in completeness
        assert 'recommendations' in completeness
        
        # Validate global score
        global_score = completeness['global_completeness_score']
        assert 0 <= global_score <= 100
        
        # Validate table completeness breakdown
        table_completeness = completeness['table_completeness']
        for table, table_data in table_completeness.items():
            assert 'average_completeness' in table_data
            assert 'record_count' in table_data
            assert 'last_updated' in table_data
            
            avg_completeness = table_data['average_completeness']
            assert 0 <= avg_completeness <= 100