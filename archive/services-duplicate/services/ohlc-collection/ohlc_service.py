#!/usr/bin/env python3
"""
OHLC Service Collector - Centralized Integration
- Integrates with shared/scheduling_config.py
- Runs as a service with proper scheduling
- Uses enhanced OHLC collection logic
"""

import os
import sys
import time
import logging
import threading
import schedule
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import centralized scheduling configuration
try:
    from shared.scheduling_config import get_collector_schedule, create_schedule_for_collector
except ImportError as e:
    logging.error(f"Could not import centralized scheduling config: {e}")
    get_collector_schedule = None
    create_schedule_for_collector = None

# Import the premium OHLC collector
from premium_ohlc_collector import PremiumOHLCCollector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OHLCService:
    """OHLC Collection Service with Centralized Scheduling"""
    
    def __init__(self):
        self.collector = PremiumOHLCCollector()
        self.running = False
        
    def collect_current_data(self):
        """Collect current OHLC data for all symbols"""
        try:
            logger.info("🔄 Starting scheduled OHLC collection...")
            
            # Run gap detection first
            self.collector.auto_gap_detection_and_backfill()
            
            # Then collect current data
            result = self.collector.collect_current_data()
            
            logger.info(f"✅ OHLC collection completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in OHLC collection: {e}")
            return False
    
    def start_service(self):
        """Start the OHLC collection service"""
        logger.info("🚀 Starting OHLC Collection Service...")
        
        # Setup centralized scheduling
        if create_schedule_for_collector:
            try:
                create_schedule_for_collector('ohlc', schedule, self.collect_current_data)
                logger.info("✅ Using centralized scheduling configuration")
            except Exception as e:
                logger.warning(f"Centralized config failed, using fallback: {e}")
                # Fallback scheduling - daily at 2 AM
                schedule.every().day.at("02:00").do(self.collect_current_data)
        else:
            logger.warning("⚠️ Centralized scheduling not available, using fallback")
            # Fallback scheduling - daily at 2 AM
            schedule.every().day.at("02:00").do(self.collect_current_data)
        
        # Run initial collection
        logger.info("🔄 Running initial OHLC collection...")
        self.collect_current_data()
        
        # Start scheduler loop
        self.running = True
        logger.info("✅ OHLC Service started - running scheduled collections...")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("⚠️ OHLC Service interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in scheduler: {e}")
                time.sleep(60)
    
    def stop_service(self):
        """Stop the service"""
        self.running = False
        logger.info("🛑 OHLC Service stopped")

def main():
    """Main entry point"""
    try:
        service = OHLCService()
        service.start_service()
    except KeyboardInterrupt:
        logger.info("⚠️ Service interrupted")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()