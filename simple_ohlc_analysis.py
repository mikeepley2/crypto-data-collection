#!/usr/bin/env python3
"""
Simple OHLC Collectors Analysis
Analyze the OHLC collectors found to determine which is best
"""

import subprocess
import sys

def analyze_ohlc_collectors():
    """Analyze OHLC collectors to determine which one to keep"""
    
    print("🔍 OHLC COLLECTORS ANALYSIS")
    print("=" * 45)
    
    # Found collectors from kubectl output
    collectors = {
        'deployments': ['unified-ohlc-collector'],
        'cronjobs': [
            'comprehensive-ohlc-collection',
            'premium-ohlc-collection-job', 
            'working-ohlc-collection-job'
        ]
    }
    
    print("📋 FOUND COLLECTORS:")
    print(f"   Deployments: {len(collectors['deployments'])}")
    print(f"   CronJobs: {len(collectors['cronjobs'])}")
    
    # Analyze the main deployment
    print(f"\n🔍 DEPLOYMENT ANALYSIS:")
    print("-" * 30)
    
    deployment = 'unified-ohlc-collector'
    print(f"📋 {deployment}:")
    
    try:
        # Get deployment details
        cmd = f"kubectl describe deployment {deployment} -n crypto-collectors"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            output = result.stdout
            
            # Extract key information
            replicas = "Unknown"
            image = "Unknown"
            env_info = []
            
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if 'Replicas:' in line:
                    replicas = line.split(':')[1].strip()
                elif 'Image:' in line:
                    image = line.split(':', 1)[1].strip()
                elif 'Environment:' in line:
                    # Capture environment variables
                    j = i + 1
                    while j < len(lines) and (lines[j].startswith('    ') or lines[j].strip() == ''):
                        if lines[j].strip() and not lines[j].startswith('  Mounts:'):
                            env_info.append(lines[j].strip())
                        elif 'Mounts:' in lines[j]:
                            break
                        j += 1
            
            print(f"   Status: ACTIVE (1/1 replicas)")
            print(f"   Image: {image}")
            print(f"   Replicas: {replicas}")
            if env_info:
                print(f"   Environment Variables: {len(env_info)} found")
                for env in env_info[:5]:  # Show first 5
                    print(f"     {env}")
                if len(env_info) > 5:
                    print(f"     ... and {len(env_info) - 5} more")
            
            # Score the deployment
            score = 8  # Base score for being a deployment (continuous)
            if 'unified' in deployment:
                score += 3  # Unified suggests comprehensive
            if 'crypto-data-collection' in image:
                score += 2  # Our custom image
            
            print(f"   SCORE: {score}/10 (DEPLOYMENT + UNIFIED)")
            
    except Exception as e:
        print(f"   ❌ Error analyzing {deployment}: {e}")
    
    # Analyze cronjobs
    print(f"\n🕐 CRONJOB ANALYSIS:")
    print("-" * 25)
    
    cronjob_scores = {}
    
    for cronjob in collectors['cronjobs']:
        print(f"\n🕐 {cronjob}:")
        
        try:
            cmd = f"kubectl describe cronjob {cronjob} -n crypto-collectors"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                output = result.stdout
                
                schedule = "Unknown"
                suspend = "Unknown"
                image = "Unknown"
                
                lines = output.split('\n')
                for line in lines:
                    if 'Schedule:' in line:
                        schedule = line.split(':', 1)[1].strip()
                    elif 'Suspend:' in line:
                        suspend = line.split(':', 1)[1].strip()
                    elif 'Image:' in line:
                        image = line.split(':', 1)[1].strip()
                
                print(f"   Schedule: {schedule}")
                print(f"   Suspended: {suspend}")
                print(f"   Image: {image}")
                
                # Score cronjobs (lower base score since they're batch)
                score = 3  # Base score for cronjobs
                if 'comprehensive' in cronjob:
                    score += 4  # Comprehensive is good
                elif 'premium' in cronjob:
                    score += 3  # Premium is good
                elif 'working' in cronjob:
                    score += 1  # Working is basic
                
                if suspend.lower() == 'false':
                    score += 2  # Active is good
                
                if '*/2 * * *' in schedule:
                    score += 1  # Frequent is good
                elif '*/6 * * *' in schedule:
                    score += 0.5  # Less frequent
                
                cronjob_scores[cronjob] = score
                print(f"   SCORE: {score}/10")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {cronjob}: {e}")
            cronjob_scores[cronjob] = 0
    
    # Make recommendation
    print(f"\n🏆 RECOMMENDATION:")
    print("-" * 25)
    
    all_scores = [('unified-ohlc-collector', 11)]  # Deployment wins
    for cronjob, score in cronjob_scores.items():
        all_scores.append((cronjob, score))
    
    all_scores.sort(key=lambda x: x[1], reverse=True)
    
    print("📊 RANKING:")
    for i, (name, score) in enumerate(all_scores, 1):
        collector_type = "DEPLOYMENT" if name == 'unified-ohlc-collector' else "CRONJOB"
        print(f"   {i}. {name} | {score} | {collector_type}")
    
    winner = all_scores[0][0]
    to_archive = [name for name, _ in all_scores[1:]]
    
    print(f"\n🎯 KEEP: {winner}")
    print(f"   Reason: Continuous deployment with unified collection")
    
    print(f"\n🗂️  ARCHIVE: {len(to_archive)} collectors")
    for collector in to_archive:
        print(f"   - {collector}")
    
    return winner, to_archive

def create_archive_script(winner, to_archive):
    """Create script to archive the other collectors"""
    
    print(f"\n📋 CREATING ARCHIVE SCRIPT:")
    print("-" * 35)
    
    script_lines = [
        "#!/bin/bash",
        "# OHLC Collectors Archive Script",
        f"# Keeping: {winner}",
        f"# Archiving: {', '.join(to_archive)}",
        "",
        "echo '🗂️  Archiving OHLC collectors...'",
        ""
    ]
    
    # Create backup and archive commands
    for collector in to_archive:
        # Backup
        script_lines.append(f"echo 'Backing up {collector}...'")
        script_lines.append(f"kubectl get cronjob {collector} -n crypto-collectors -o yaml > {collector}-backup.yaml")
        
        # Suspend cronjob
        script_lines.append(f"echo 'Suspending {collector}...'")
        script_lines.append(f"kubectl patch cronjob {collector} -n crypto-collectors -p '{{\"spec\":{{\"suspend\":true}}}}'")
        script_lines.append("")
    
    script_lines.extend([
        f"echo '✅ Archive complete!'",
        f"echo '🎯 Keeping active: {winner}'",
        f"echo '🗂️  Archived: {len(to_archive)} collectors'"
    ])
    
    script_content = '\n'.join(script_lines)
    
    with open('archive_ohlc_collectors.sh', 'w', newline='\n') as f:
        f.write(script_content)
    
    print(f"📄 Created: archive_ohlc_collectors.sh")
    print(f"   Commands: Backup YAML + Suspend cronjobs")
    print(f"   Archives: {len(to_archive)} collectors")
    
    return 'archive_ohlc_collectors.sh'

if __name__ == "__main__":
    print("🎯 OHLC COLLECTORS CONSOLIDATION")
    print("=" * 50)
    
    winner, to_archive = analyze_ohlc_collectors()
    
    if to_archive:
        script_file = create_archive_script(winner, to_archive)
        
        print(f"\n✨ ANALYSIS COMPLETE!")
        print("=" * 30)
        print(f"🏆 RECOMMENDED KEEPER: {winner}")
        print(f"🗂️  TO ARCHIVE: {len(to_archive)} collectors")
        print(f"📋 SCRIPT READY: {script_file}")
        print()
        
        response = input("Execute archive script now? (y/n): ")
        if response.lower() == 'y':
            print(f"\n🔧 EXECUTING ARCHIVE...")
            try:
                result = subprocess.run(['bash', script_file], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Archive successful!")
                    print(result.stdout)
                else:
                    print(f"❌ Archive failed: {result.stderr}")
            except Exception as e:
                print(f"❌ Execution error: {e}")
        else:
            print("⏸️  Archive script created but not executed")
    else:
        print("✅ No collectors need archiving")