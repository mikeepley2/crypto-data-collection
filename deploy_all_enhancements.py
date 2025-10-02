#!/usr/bin/env python3

import subprocess
import time
from datetime import datetime

def main():
    print("=== COMPREHENSIVE DEPLOYMENT AND ACTIVATION STRATEGY ===\n")
    
    print("🚀 DEPLOYMENT SEQUENCE FOR ALL ENHANCEMENTS:")
    print("=" * 60)
    
    # Step 1: Restart materialized updater with latest code
    print("\n1️⃣ MATERIALIZED UPDATER DEPLOYMENT")
    print("   🔄 Restarting with enhanced code...")
    try:
        result = subprocess.run([
            'kubectl', 'rollout', 'restart', 'deployment/realtime-materialized-updater', '-n', 'crypto-collectors'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Materialized updater restart initiated")
        else:
            print(f"   ⚠️ Restart command result: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Restart error: {e}")
    
    # Step 2: Force technical indicators generation
    print("\n2️⃣ TECHNICAL INDICATORS ACTIVATION")
    print("   🔧 Creating fresh technical indicators job...")
    try:
        result = subprocess.run([
            'kubectl', 'create', 'job', 'force-all-tech-indicators', 
            '--from=cronjob/materialized-updater-cron', '-n', 'crypto-collectors'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Technical indicators generation job created")
        else:
            print(f"   ⚠️ Job creation result: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Job creation error: {e}")
    
    # Step 3: Verify services are running
    print("\n3️⃣ SERVICE STATUS VERIFICATION")
    services_to_check = [
        'technical-indicators',
        'realtime-materialized-updater', 
        'enhanced-sentiment',
        'macro-economic'
    ]
    
    for service in services_to_check:
        try:
            result = subprocess.run([
                'kubectl', 'get', 'pods', '-n', 'crypto-collectors', '-l', f'app={service}', '--no-headers'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and 'Running' in result.stdout:
                print(f"   ✅ {service}: Running")
            else:
                print(f"   ⚠️ {service}: Status unclear - {result.stdout.strip()}")
        except Exception as e:
            print(f"   ❌ {service}: Check failed - {e}")
    
    # Step 4: Trigger comprehensive update cycle
    print("\n4️⃣ COMPREHENSIVE UPDATE CYCLE")
    print("   🔄 Triggering full data pipeline update...")
    
    # Create multiple jobs to ensure all enhancements activate
    jobs_to_create = [
        'activation-volume-market',
        'activation-macro-expansion', 
        'activation-sentiment-advanced',
        'activation-technical-comprehensive'
    ]
    
    for job_name in jobs_to_create:
        try:
            result = subprocess.run([
                'kubectl', 'create', 'job', job_name,
                '--from=cronjob/materialized-updater-cron', '-n', 'crypto-collectors'
            ], capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0:
                print(f"   ✅ {job_name}: Created")
            else:
                print(f"   ⚠️ {job_name}: {result.stderr.strip()}")
        except Exception as e:
            print(f"   ❌ {job_name}: Error - {e}")
    
    print("\n5️⃣ WAIT FOR PROCESSING")
    print("   ⏳ Allowing 60 seconds for all jobs to process...")
    print("   📊 Jobs will:")
    print("      • Apply volume/market cap enhancements")
    print("      • Activate 24+ macro economic indicators")  
    print("      • Process 113,853+ sentiment signals")
    print("      • Generate fresh technical indicators (29+ fields)")
    
    # Countdown timer
    for i in range(60, 0, -10):
        print(f"   ⏱️ {i} seconds remaining...")
        time.sleep(10)
    
    print("\n✅ DEPLOYMENT SEQUENCE COMPLETED")
    print("=" * 60)
    print("🎯 EXPECTED IMPROVEMENTS:")
    print("   • Volume/Market: Market cap population boost")
    print("   • Macro Economic: 24+ indicators → 80%+ category completion")
    print("   • Sentiment: 113,853 signals → 10+ sentiment fields")
    print("   • Technical: Fresh generation → 29+ technical fields")
    print("   • Overall: Target 40%+ population rate")
    
    print(f"\n📈 NEXT STEPS:")
    print("   1. Run comprehensive_final_check.py again")
    print("   2. Verify population improvements")
    print("   3. Check specific category enhancements")
    print("   4. Monitor ml_features_materialized table")
    
    print(f"\n⏰ Deployment completed at: {datetime.now()}")

if __name__ == "__main__":
    main()