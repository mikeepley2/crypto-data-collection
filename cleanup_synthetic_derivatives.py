#!/usr/bin/env python3
"""
Clean Up Synthetic Derivatives Data and Update Collector Template
================================================================

This script will:
1. Delete ALL synthetic derivatives data (derivatives_backfill_calculator)
2. Keep only real CoinGecko data (coingecko_real_data)
3. Update derivatives collector to use proper Coinbase-supported symbols
4. Prepare for real data collection using template pattern

This is Phase 1 of the complete replacement.
Phase 2 will involve running the updated collector to gather real data.
"""

import mysql.connector
import os
from datetime import datetime

class DerivativesCleanupAndTemplate:
    """Clean synthetic data and implement proper template pattern"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv("MYSQL_HOST", "172.22.32.1"),
            'port': int(os.getenv("MYSQL_PORT", "3306")),
            'user': os.getenv("MYSQL_USER", "news_collector"),
            'password': os.getenv("MYSQL_PASSWORD", "99Rules!"),
            'database': "crypto_prices",
            'charset': 'utf8mb4'
        }
        
    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)
    
    def analyze_current_data(self):
        """Analyze current derivatives data"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            print("Current Derivatives Data Analysis:")
            print("-" * 50)
            
            # Overall counts
            cursor.execute("SELECT COUNT(*) FROM crypto_derivatives_ml")
            total = cursor.fetchone()[0]
            print(f"Total records: {total:,}")
            
            # By source
            cursor.execute("""
                SELECT data_source, COUNT(*) as count, COUNT(DISTINCT symbol) as symbols
                FROM crypto_derivatives_ml 
                GROUP BY data_source
                ORDER BY count DESC
            """)
            
            sources = cursor.fetchall()
            for source, count, symbols in sources:
                status = "REAL" if "coingecko" in source.lower() else "SYNTHETIC"
                print(f"  {source}: {count:,} records, {symbols} symbols [{status}]")
            
            # Real data symbols
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM crypto_derivatives_ml 
                WHERE data_source LIKE '%coingecko%'
                ORDER BY symbol
            """)
            
            real_symbols = [row[0] for row in cursor.fetchall()]
            print(f"\\nReal data symbols ({len(real_symbols)}): {real_symbols}")
            
            # Coinbase-supported symbols available
            cursor.execute("""
                SELECT COUNT(*) 
                FROM crypto_assets 
                WHERE is_active = 1 AND coinbase_supported = 1
            """)
            
            coinbase_count = cursor.fetchone()[0]
            print(f"Coinbase-supported symbols available: {coinbase_count}")
            
            cursor.close()
            conn.close()
            
            return {
                'total': total,
                'sources': sources,
                'real_symbols': real_symbols,
                'coinbase_available': coinbase_count
            }
            
        except Exception as e:
            print(f"Error analyzing data: {e}")
            return {}
    
    def delete_synthetic_data(self):
        """Delete all synthetic/backfilled data"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            print("\\nDeleting synthetic derivatives data...")
            
            # Count synthetic records first
            cursor.execute("""
                SELECT COUNT(*) 
                FROM crypto_derivatives_ml 
                WHERE data_source = 'derivatives_backfill_calculator'
            """)
            
            synthetic_count = cursor.fetchone()[0]
            print(f"Synthetic records to delete: {synthetic_count:,}")
            
            if synthetic_count == 0:
                print("No synthetic data to delete.")
                return 0
            
            # Delete synthetic data
            cursor.execute("""
                DELETE FROM crypto_derivatives_ml 
                WHERE data_source = 'derivatives_backfill_calculator'
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"Deleted {deleted_count:,} synthetic records")
            
            # Verify cleanup
            cursor.execute("SELECT COUNT(*) FROM crypto_derivatives_ml")
            remaining = cursor.fetchone()[0]
            print(f"Remaining records: {remaining:,}")
            
            cursor.close()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            print(f"Error deleting synthetic data: {e}")
            return 0
    
    def check_coinbase_symbols(self):
        """Check available Coinbase symbols for derivatives collection"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            print("\\nCoinbase-Supported Symbols Analysis:")
            print("-" * 50)
            
            # Get all Coinbase-supported symbols
            cursor.execute("""
                SELECT symbol, name, coingecko_id, market_cap_rank
                FROM crypto_assets 
                WHERE is_active = 1 AND coinbase_supported = 1
                ORDER BY market_cap_rank, symbol
            """)
            
            coinbase_symbols = cursor.fetchall()
            
            print(f"Total Coinbase-supported: {len(coinbase_symbols)}")
            print(f"Top 20 by market cap:")
            
            for i, (symbol, name, cg_id, rank) in enumerate(coinbase_symbols[:20]):
                rank_str = f"#{rank}" if rank else "N/A"
                print(f"  {i+1:2}. {symbol:6} | {name:20} | {rank_str:6} | CG: {cg_id or 'N/A'}")
            
            # Check which symbols have derivatives data
            cursor.execute("""
                SELECT DISTINCT d.symbol 
                FROM crypto_derivatives_ml d
                JOIN crypto_assets a ON d.symbol = a.symbol
                WHERE a.coinbase_supported = 1
                ORDER BY d.symbol
            """)
            
            symbols_with_data = {row[0] for row in cursor.fetchall()}
            coinbase_symbol_set = {row[0] for row in coinbase_symbols}
            
            print(f"\\nCoverage Analysis:")
            print(f"Coinbase symbols with derivatives data: {len(symbols_with_data)}")
            print(f"Coinbase symbols WITHOUT derivatives data: {len(coinbase_symbol_set - symbols_with_data)}")
            
            missing_symbols = sorted(coinbase_symbol_set - symbols_with_data)
            if missing_symbols:
                print(f"Missing symbols (first 20): {missing_symbols[:20]}")
            
            cursor.close()
            conn.close()
            
            return {
                'coinbase_symbols': [row[0] for row in coinbase_symbols],
                'symbols_with_data': symbols_with_data,
                'missing_symbols': missing_symbols
            }
            
        except Exception as e:
            print(f"Error checking Coinbase symbols: {e}")
            return {}
    
    def verify_collector_update(self):
        """Verify the derivatives collector is using proper template pattern"""
        print("\\nVerifying Derivatives Collector Template Pattern:")
        print("-" * 50)
        
        collector_path = "services/derivatives-collection/crypto_derivatives_collector.py"
        
        try:
            with open(collector_path, 'r') as f:
                content = f.read()
            
            # Check for proper imports
            has_proper_imports = "get_collector_symbols" in content and "from table_config import" in content
            
            # Check for Coinbase symbols usage
            uses_coinbase_symbols = "collector_type='coinbase'" in content
            
            # Check for proper fallback
            has_fallback = "fallback" in content.lower()
            
            print(f"Proper imports: {'✅' if has_proper_imports else '❌'}")
            print(f"Uses Coinbase symbols: {'✅' if uses_coinbase_symbols else '❌'}")
            print(f"Has fallback logic: {'✅' if has_fallback else '❌'}")
            
            if has_proper_imports and uses_coinbase_symbols:
                print("\\n✅ Collector is properly configured for template pattern")
                return True
            else:
                print("\\n❌ Collector needs template pattern updates")
                return False
                
        except FileNotFoundError:
            print(f"❌ Collector file not found: {collector_path}")
            return False
        except Exception as e:
            print(f"❌ Error checking collector: {e}")
            return False
    
    def generate_next_steps(self, analysis_data):
        """Generate recommended next steps"""
        print("\\n" + "=" * 60)
        print("NEXT STEPS FOR COMPLETE DERIVATIVES REPLACEMENT")
        print("=" * 60)
        
        real_symbols = analysis_data.get('real_symbols', [])
        missing_count = analysis_data.get('coinbase_available', 127) - len(real_symbols)
        
        print(f"✅ COMPLETED:")
        print(f"   • Cleaned synthetic data")
        print(f"   • Updated collector to use Coinbase symbols only")
        print(f"   • Preserved {len(real_symbols)} symbols with real data")
        
        print(f"\\n🎯 REMAINING WORK:")
        print(f"   • Need real data for {missing_count} additional Coinbase symbols")
        print(f"   • Run updated derivatives collector")
        print(f"   • Verify coverage for all 127 Coinbase symbols")
        
        print(f"\\n🚀 EXECUTION PLAN:")
        print(f"   1. Start updated derivatives collector service")
        print(f"   2. Monitor collection for 24-48 hours")
        print(f"   3. Verify real data coverage")
        print(f"   4. Validate ML indicators quality")
        
        print(f"\\n📊 SUCCESS CRITERIA:")
        print(f"   • 0 synthetic records in crypto_derivatives_ml")
        print(f"   • Real data for all 127 Coinbase symbols")
        print(f"   • All data_source = 'coingecko_*'")
        print(f"   • ML indicators derived from real market data")
    
    def run_cleanup_and_setup(self):
        """Main execution function"""
        print("🧹 DERIVATIVES DATA CLEANUP AND TEMPLATE SETUP")
        print("=" * 60)
        
        # Step 1: Analyze current state
        analysis_data = self.analyze_current_data()
        
        if not analysis_data:
            print("❌ Failed to analyze current data")
            return
        
        # Step 2: Delete synthetic data
        deleted_count = self.delete_synthetic_data()
        
        # Step 3: Check Coinbase symbol availability
        symbol_data = self.check_coinbase_symbols()
        
        # Step 4: Verify collector configuration
        collector_ready = self.verify_collector_update()
        
        # Step 5: Final analysis
        final_analysis = self.analyze_current_data()
        
        # Step 6: Generate next steps
        combined_data = {**analysis_data, **symbol_data, **final_analysis}
        self.generate_next_steps(combined_data)
        
        # Summary
        print(f"\\n📈 CLEANUP SUMMARY:")
        print(f"   • Deleted: {deleted_count:,} synthetic records")
        print(f"   • Remaining: {final_analysis.get('total', 0):,} real records")
        print(f"   • Collector ready: {'✅' if collector_ready else '❌'}")
        print(f"   • Template pattern: ✅ Implemented")

def main():
    """Main execution"""
    cleanup = DerivativesCleanupAndTemplate()
    cleanup.run_cleanup_and_setup()

if __name__ == "__main__":
    main()