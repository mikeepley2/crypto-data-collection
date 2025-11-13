"""
Generic Data Collector Template with Placeholder Creation
=========================================================

This template provides a standardized pattern for creating data collectors
that include automatic placeholder record creation for completeness tracking.

Key Features:
- Automatic placeholder creation for expected data points
- Completeness percentage calculation and updates  
- Gap detection and automatic backfill triggers
- Health monitoring and error handling
- Standardized logging and metrics
- FastAPI integration for monitoring/control endpoints

Usage:
1. Copy this template for new collectors
2. Customize the collector-specific methods (marked with TODO)
3. Update the schema/table definitions
4. Configure collection schedule and data sources
"""

import os
import sys
import time
import logging
import mysql.connector
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from decimal import Decimal
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import schedule


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseDataCollectorWithPlaceholders:
    """
    Base template for data collectors with automatic placeholder creation
    
    This template implements:
    - Automatic placeholder record creation
    - Completeness percentage tracking  
    - Gap detection and backfill
    - Health monitoring
    - FastAPI endpoints for control/monitoring
    """
    
    def __init__(self):
        # Service identification
        self.service_name = "base-collector"  # TODO: Override in subclass
        self.version = "1.0.0"
        
        # Database configuration
        self.db_config = {
            'host': os.getenv("DB_HOST", "127.0.0.1"),
            'user': os.getenv("DB_USER", "news_collector"),
            'password': os.getenv("DB_PASSWORD", "99Rules!"),
            'database': os.getenv("DB_NAME", "crypto_prices"),
            'charset': 'utf8mb4',
            'autocommit': False
        }
        
        # Collection configuration
        self.collection_interval = self.get_collection_interval()
        self.enable_placeholders = os.getenv("ENSURE_PLACEHOLDERS", "true").lower() == "true"
        self.placeholder_lookback = self.get_placeholder_lookback()
        self.max_backfill_limit = self.get_max_backfill_limit()
        
        # Statistics tracking
        self.stats = {
            'total_collected': 0,
            'total_placeholders_created': 0,
            'collection_errors': 0,
            'last_collection': None,
            'last_gap_check': None,
            'health_score': 0.0,
            'service_start_time': datetime.now()
        }
        
        # FastAPI app for monitoring/control
        self.app = FastAPI(title=f"{self.service_name} API")
        self.setup_routes()
        
        logger.info(f"✅ {self.service_name} v{self.version} initialized")
        logger.info(f"   Placeholders enabled: {self.enable_placeholders}")
        logger.info(f"   Collection interval: {self.collection_interval}")
        logger.info(f"   Placeholder lookback: {self.placeholder_lookback}")
    
    # =============================================================================
    # ABSTRACT METHODS - MUST BE IMPLEMENTED BY SUBCLASSES
    # =============================================================================
    
    def get_collection_interval(self) -> str:
        """Return collection interval (e.g., '5min', '1hour', '6hour', '1day')"""
        # TODO: Override in subclass
        return "1hour"
    
    def get_placeholder_lookback(self) -> int:
        """Return how far back to create placeholders (in appropriate units)"""
        # TODO: Override in subclass - days/hours based on collection frequency
        return 7  # days
    
    def get_max_backfill_limit(self) -> int:
        """Return maximum backfill period to prevent runaway backfills"""
        # TODO: Override in subclass
        return 30  # days
    
    def get_expected_data_points(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Return list of expected data points that should exist for the given time range
        
        Returns: List of dicts with keys like:
        - {'symbol': 'BTC', 'timestamp': datetime, 'data_type': 'price'}
        - {'indicator': 'VIX', 'date': date, 'frequency': 'daily'}
        """
        # TODO: Implement in subclass
        raise NotImplementedError("Subclass must implement get_expected_data_points")
    
    def create_placeholder_record(self, data_point: Dict) -> bool:
        """
        Create a placeholder record for the given data point
        
        Args:
            data_point: Dict describing the expected data point
            
        Returns:
            True if placeholder was created, False otherwise
        """
        # TODO: Implement in subclass
        raise NotImplementedError("Subclass must implement create_placeholder_record")
    
    def collect_real_data(self, backfill_days: Optional[int] = None) -> int:
        """
        Collect real data from APIs/sources and update existing placeholders
        
        Args:
            backfill_days: If set, backfill last N days instead of just current
            
        Returns:
            Number of records collected/updated
        """
        # TODO: Implement in subclass  
        raise NotImplementedError("Subclass must implement collect_real_data")
    
    def calculate_record_completeness(self, record_data: Dict) -> float:
        """
        Calculate completeness percentage for a single record
        
        Args:
            record_data: Dict containing the record's field values
            
        Returns:
            Completeness percentage (0.0 to 100.0)
        """
        # TODO: Implement in subclass - analyze which fields are populated
        total_fields = len(record_data)
        populated_fields = sum(1 for v in record_data.values() if v is not None)
        return (populated_fields / total_fields) * 100.0 if total_fields > 0 else 0.0
    
    def get_table_name(self) -> str:
        """Return the primary table name for this collector"""
        # TODO: Override in subclass
        return "generic_data"
    
    # =============================================================================
    # PLACEHOLDER MANAGEMENT METHODS
    # =============================================================================
    
    def ensure_placeholder_records(self, target_datetime: Optional[datetime] = None) -> int:
        """
        Ensure placeholder records exist for expected data points
        
        Args:
            target_datetime: Specific datetime to create placeholders for.
                           If None, uses current time and lookback period.
                           
        Returns:
            Number of placeholder records created
        """
        if not self.enable_placeholders:
            logger.debug("Placeholder creation disabled")
            return 0
        
        logger.info("🔧 Ensuring placeholder records exist...")
        
        conn = self.get_db_connection()
        if not conn:
            logger.error("Failed to get database connection for placeholder creation")
            return 0
        
        try:
            cursor = conn.cursor()
            placeholders_created = 0
            
            # Determine time range for placeholder creation
            if target_datetime:
                start_time = target_datetime
                end_time = target_datetime
            else:
                end_time = datetime.now()
                if self.collection_interval.endswith('min'):
                    minutes = int(self.collection_interval.replace('min', ''))
                    start_time = end_time - timedelta(hours=self.placeholder_lookback)
                elif self.collection_interval.endswith('hour'):
                    start_time = end_time - timedelta(hours=self.placeholder_lookback)
                else:  # daily or longer
                    start_time = end_time - timedelta(days=self.placeholder_lookback)
            
            # Get expected data points for this time range
            expected_points = self.get_expected_data_points(start_time, end_time)
            
            logger.info(f"   Expected data points: {len(expected_points)}")
            
            # Create placeholders for each expected data point
            for data_point in expected_points:
                try:
                    if self.create_placeholder_record(data_point):
                        placeholders_created += 1
                except Exception as e:
                    logger.debug(f"Error creating placeholder for {data_point}: {e}")
            
            conn.commit()
            
            self.stats['total_placeholders_created'] += placeholders_created
            logger.info(f"✅ Created {placeholders_created} placeholder records")
            
            return placeholders_created
            
        except Exception as e:
            logger.error(f"Error ensuring placeholder records: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def update_record_completeness(self, record_identifier: Dict, record_data: Dict) -> bool:
        """
        Update the completeness percentage for a specific record
        
        Args:
            record_identifier: Dict with keys to identify the record (e.g., symbol, timestamp)
            record_data: Dict with the record's current field values
            
        Returns:
            True if update was successful
        """
        completeness = self.calculate_record_completeness(record_data)
        
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Build WHERE clause from identifier
            where_conditions = []
            where_values = []
            for key, value in record_identifier.items():
                where_conditions.append(f"{key} = %s")
                where_values.append(value)
            
            where_clause = " AND ".join(where_conditions)
            
            # Update completeness percentage
            update_sql = f"""
                UPDATE {self.get_table_name()}
                SET data_completeness_percentage = %s, 
                    updated_at = NOW()
                WHERE {where_clause}
            """
            
            cursor.execute(update_sql, [completeness] + where_values)
            success = cursor.rowcount > 0
            
            conn.commit()
            return success
            
        except Exception as e:
            logger.error(f"Error updating completeness for {record_identifier}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    # =============================================================================
    # COLLECTION ORCHESTRATION METHODS  
    # =============================================================================
    
    def run_collection_with_placeholders(self, backfill_days: Optional[int] = None) -> Dict[str, int]:
        """
        Run complete collection cycle with placeholder creation
        
        Args:
            backfill_days: If set, backfill last N days instead of just current
            
        Returns:
            Dict with collection statistics
        """
        logger.info(f"🚀 Starting collection cycle for {self.service_name}")
        start_time = datetime.now()
        
        try:
            # Step 1: Ensure placeholder records exist
            placeholders_created = 0
            if self.enable_placeholders:
                placeholders_created = self.ensure_placeholder_records()
            
            # Step 2: Collect real data and update placeholders  
            records_collected = self.collect_real_data(backfill_days)
            
            # Step 3: Update statistics
            self.stats['total_collected'] += records_collected
            self.stats['last_collection'] = datetime.now()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Collection cycle completed in {duration:.1f}s")
            logger.info(f"   Records collected: {records_collected}")
            logger.info(f"   Placeholders created: {placeholders_created}")
            
            return {
                'status': 'success',
                'records_collected': records_collected,
                'placeholders_created': placeholders_created,
                'duration_seconds': duration
            }
            
        except Exception as e:
            logger.error(f"Collection cycle failed: {e}")
            self.stats['collection_errors'] += 1
            
            return {
                'status': 'error',
                'error': str(e),
                'records_collected': 0,
                'placeholders_created': 0
            }
    
    def detect_gap(self) -> Optional[float]:
        """
        Detect time gap since last successful data collection
        
        Returns:
            Gap in hours, or None if no previous data found
        """
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Find the most recent record with actual data (not just placeholders)
            cursor.execute(f"""
                SELECT MAX(updated_at) as last_update
                FROM {self.get_table_name()}
                WHERE data_completeness_percentage > 0
                AND updated_at IS NOT NULL
            """)
            
            result = cursor.fetchone()
            if not result or not result[0]:
                logger.info("No previous data found for gap detection")
                return None
            
            last_update = result[0]
            gap_hours = (datetime.now() - last_update).total_seconds() / 3600
            
            logger.info(f"Gap detection: {gap_hours:.1f} hours since last update")
            return gap_hours
            
        except Exception as e:
            logger.error(f"Error detecting gap: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def auto_gap_detection_and_backfill(self):
        """
        Automatically detect gaps and trigger backfill if needed
        """
        logger.info("🔍 Running automatic gap detection...")
        
        gap_hours = self.detect_gap()
        self.stats['last_gap_check'] = datetime.now()
        
        if gap_hours is None:
            logger.info("No previous data found - running initial collection")
            self.run_collection_with_placeholders()
            return
        
        # Determine expected collection frequency in hours
        if self.collection_interval.endswith('min'):
            expected_interval_hours = int(self.collection_interval.replace('min', '')) / 60
        elif self.collection_interval.endswith('hour'):
            expected_interval_hours = int(self.collection_interval.replace('hour', ''))
        else:
            expected_interval_hours = 24  # daily
        
        # Trigger backfill if gap is significant
        if gap_hours > expected_interval_hours * 2:  # Allow some tolerance
            gap_days = min(int(gap_hours / 24) + 1, self.max_backfill_limit)
            
            logger.warning(f"⚠️  Significant gap detected: {gap_hours:.1f} hours")
            logger.info(f"🔄 Triggering automatic backfill for {gap_days} days...")
            
            self.run_collection_with_placeholders(backfill_days=gap_days)
            logger.info("✅ Automatic backfill completed")
        else:
            logger.info(f"✅ No significant gap ({gap_hours:.1f} hours)")
    
    # =============================================================================
    # HEALTH MONITORING METHODS
    # =============================================================================
    
    def calculate_health_score(self) -> float:
        """
        Calculate overall health score (0.0 to 100.0) based on:
        - Data freshness
        - Collection success rate  
        - Error rate
        - Completeness percentage
        """
        try:
            conn = self.get_db_connection()
            if not conn:
                return 0.0
            
            cursor = conn.cursor()
            
            # Factor 1: Data freshness (40% weight)
            gap_hours = self.detect_gap() or 0
            expected_interval_hours = 1  # Default to hourly
            if self.collection_interval.endswith('min'):
                expected_interval_hours = int(self.collection_interval.replace('min', '')) / 60
            elif self.collection_interval.endswith('hour'):
                expected_interval_hours = int(self.collection_interval.replace('hour', ''))
            
            freshness_score = max(0, 100 - (gap_hours / expected_interval_hours) * 20)
            
            # Factor 2: Recent completeness (40% weight)
            cursor.execute(f"""
                SELECT AVG(data_completeness_percentage) as avg_completeness
                FROM {self.get_table_name()}
                WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """)
            
            result = cursor.fetchone()
            completeness_score = float(result[0] or 0) if result else 0.0
            
            # Factor 3: Error rate (20% weight)
            total_operations = self.stats['total_collected'] + self.stats['collection_errors']
            if total_operations > 0:
                error_rate = self.stats['collection_errors'] / total_operations
                error_score = max(0, 100 - error_rate * 200)  # Penalize errors heavily
            else:
                error_score = 100.0
            
            # Calculate weighted health score
            health_score = (
                freshness_score * 0.4 +
                completeness_score * 0.4 +
                error_score * 0.2
            )
            
            self.stats['health_score'] = health_score
            return health_score
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_db_connection(self):
        """Get database connection with error handling"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def write_health_file(self):
        """Write health status to file for Kubernetes health checks"""
        try:
            health_score = self.calculate_health_score()
            with open(f"/tmp/{self.service_name}_health.txt", "w") as f:
                f.write(f"{datetime.now().isoformat()},{health_score:.1f}")
        except Exception as e:
            logger.debug(f"Error writing health file: {e}")
    
    # =============================================================================
    # FASTAPI ROUTES FOR MONITORING/CONTROL
    # =============================================================================
    
    def setup_routes(self):
        """Setup FastAPI routes for monitoring and control"""
        
        @self.app.get("/health")
        def health():
            """Kubernetes health check endpoint"""
            return {"status": "ok", "service": self.service_name}
        
        @self.app.get("/status")
        def status():
            """Detailed service status"""
            gap_hours = self.detect_gap()
            health_score = self.calculate_health_score()
            
            return {
                "service": self.service_name,
                "version": self.version,
                "stats": self.stats,
                "config": {
                    "collection_interval": self.collection_interval,
                    "placeholders_enabled": self.enable_placeholders,
                    "placeholder_lookback": self.placeholder_lookback
                },
                "health": {
                    "score": health_score,
                    "gap_hours": gap_hours,
                    "status": "healthy" if health_score > 70 else "degraded"
                }
            }
        
        @self.app.post("/collect")
        def trigger_collection(background_tasks: BackgroundTasks):
            """Manually trigger data collection"""
            background_tasks.add_task(self.run_collection_with_placeholders)
            return {"status": "started", "message": "Collection initiated"}
        
        @self.app.post("/collect/{days}")
        def trigger_backfill(days: int, background_tasks: BackgroundTasks):
            """Manually trigger backfill for specified days"""
            if days > self.max_backfill_limit:
                return {"error": f"Maximum backfill period is {self.max_backfill_limit} days"}
            
            background_tasks.add_task(self.run_collection_with_placeholders, days)
            return {"status": "started", "message": f"Backfill initiated for {days} days"}
        
        @self.app.post("/placeholders")
        def create_placeholders(background_tasks: BackgroundTasks):
            """Manually trigger placeholder creation"""
            background_tasks.add_task(self.ensure_placeholder_records)
            return {"status": "started", "message": "Placeholder creation initiated"}
        
        @self.app.post("/gap-check")
        def gap_check():
            """Check for data gaps and optionally backfill"""
            self.auto_gap_detection_and_backfill()
            return {
                "status": "completed",
                "gap_hours": self.stats.get("gap_hours_detected", 0),
                "health_score": self.stats.get("health_score", 0)
            }
        
        @self.app.get("/metrics")
        def prometheus_metrics():
            """Prometheus metrics endpoint"""
            health_score = self.calculate_health_score()
            gap_hours = self.detect_gap() or 0
            
            metrics = f"""# HELP {self.service_name}_total_collected Total records collected
# TYPE {self.service_name}_total_collected counter
{self.service_name}_total_collected {self.stats['total_collected']}

# HELP {self.service_name}_placeholders_created Total placeholder records created
# TYPE {self.service_name}_placeholders_created counter
{self.service_name}_placeholders_created {self.stats['total_placeholders_created']}

# HELP {self.service_name}_collection_errors Total collection errors
# TYPE {self.service_name}_collection_errors counter
{self.service_name}_collection_errors {self.stats['collection_errors']}

# HELP {self.service_name}_health_score Service health score (0-100)
# TYPE {self.service_name}_health_score gauge
{self.service_name}_health_score {health_score:.1f}

# HELP {self.service_name}_gap_hours Hours since last successful collection
# TYPE {self.service_name}_gap_hours gauge
{self.service_name}_gap_hours {gap_hours:.1f}

# HELP {self.service_name}_running Service running status
# TYPE {self.service_name}_running gauge
{self.service_name}_running 1
"""
            return JSONResponse(content=metrics, media_type="text/plain")
    
    # =============================================================================
    # MAIN EXECUTION METHODS
    # =============================================================================
    
    def run_scheduler(self):
        """Run the scheduled collection process"""
        logger.info(f"🕐 Starting scheduler for {self.service_name}")
        logger.info(f"   Collection interval: {self.collection_interval}")
        
        # Auto-detect and backfill gaps on startup
        self.auto_gap_detection_and_backfill()
        
        # Schedule regular collection based on interval
        if self.collection_interval.endswith('min'):
            minutes = int(self.collection_interval.replace('min', ''))
            schedule.every(minutes).minutes.do(self.run_collection_with_placeholders)
        elif self.collection_interval.endswith('hour'):
            hours = int(self.collection_interval.replace('hour', ''))
            schedule.every(hours).hours.do(self.run_collection_with_placeholders)
        else:  # daily
            schedule.every().day.do(self.run_collection_with_placeholders)
        
        # Schedule health monitoring  
        schedule.every(5).minutes.do(self.write_health_file)
        
        # Run scheduler
        while True:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait longer on errors


# =============================================================================
# EXAMPLE IMPLEMENTATION FOR REFERENCE
# =============================================================================

class ExampleMacroCollector(BaseDataCollectorWithPlaceholders):
    """
    Example implementation for macro economic indicators
    """
    
    def __init__(self):
        self.service_name = "macro-collector"
        self.macro_indicators = ['VIX', 'DXY', 'FEDFUNDS', 'DGS10', 'UNRATE']
        super().__init__()
    
    def get_collection_interval(self) -> str:
        return "1hour"
    
    def get_placeholder_lookback(self) -> int:
        return 7  # days
    
    def get_expected_data_points(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Generate expected macro indicator data points for date range"""
        data_points = []
        
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            for indicator in self.macro_indicators:
                data_points.append({
                    'indicator_name': indicator,
                    'indicator_date': current_date,
                    'data_type': 'macro'
                })
            current_date += timedelta(days=1)
        
        return data_points
    
    def create_placeholder_record(self, data_point: Dict) -> bool:
        """Create macro indicator placeholder record"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT IGNORE INTO macro_indicators 
                (indicator_name, indicator_date, value, data_source, 
                 data_completeness_percentage, created_at)
                VALUES (%s, %s, NULL, 'placeholder_auto', 0.0, NOW())
            """, (data_point['indicator_name'], data_point['indicator_date']))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
            
        except Exception as e:
            logger.debug(f"Error creating macro placeholder: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def collect_real_data(self, backfill_days: Optional[int] = None) -> int:
        """Collect real macro data from FRED API"""
        # TODO: Implement actual FRED API collection
        logger.info(f"Collecting macro data (backfill_days={backfill_days})")
        return 0  # Placeholder
    
    def get_table_name(self) -> str:
        return "macro_indicators"


if __name__ == "__main__":
    """
    Main execution entry point
    
    Usage examples:
    python collector_template.py                    # Normal scheduled operation
    python collector_template.py --backfill 30     # Backfill last 30 days
    python collector_template.py --test            # Test mode
    """
    
    # Example usage - replace with your actual collector implementation
    collector = ExampleMacroCollector()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--backfill' and len(sys.argv) > 2:
            days = int(sys.argv[2])
            logger.info(f"🔄 BACKFILL MODE: Processing last {days} days")
            result = collector.run_collection_with_placeholders(backfill_days=days)
            logger.info(f"Backfill result: {result}")
        elif sys.argv[1] == '--test':
            logger.info("🧪 TEST MODE: Running single collection cycle")
            result = collector.run_collection_with_placeholders()
            logger.info(f"Test result: {result}")
        else:
            logger.error(f"Unknown argument: {sys.argv[1]}")
            sys.exit(1)
    else:
        # Normal scheduled operation
        collector.run_scheduler()