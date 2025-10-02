#!/usr/bin/env python3
"""
OHLC Collectors Audit and Consolidation
Find all OHLC collectors and determine which one to keep
"""

import subprocess
import json
import yaml

def audit_ohlc_collectors():
    """Audit all OHLC collectors to determine the best one to keep"""
    
    print("🔍 OHLC COLLECTORS AUDIT")
    print("=" * 50)
    
    # Get all deployments and jobs related to OHLC
    print("1. FINDING OHLC COLLECTORS:")
    print("-" * 30)
    
    try:
        # Get all deployments
        cmd = "kubectl get deployments -n crypto-collectors -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        ohlc_deployments = []
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for item in data.get('items', []):
                name = item['metadata']['name']
                if 'ohlc' in name.lower():
                    ohlc_deployments.append(name)
                    print(f"   📋 Deployment: {name}")
        
        # Get all jobs
        cmd = "kubectl get jobs -n crypto-collectors -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        ohlc_jobs = []
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for item in data.get('items', []):
                name = item['metadata']['name']
                if 'ohlc' in name.lower():
                    ohlc_jobs.append(name)
                    print(f"   ⏰ Job: {name}")
        
        # Get all cronjobs
        cmd = "kubectl get cronjobs -n crypto-collectors -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        ohlc_cronjobs = []
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for item in data.get('items', []):
                name = item['metadata']['name']
                if 'ohlc' in name.lower():
                    ohlc_cronjobs.append(name)
                    print(f"   🕐 CronJob: {name}")
        
        all_ohlc = ohlc_deployments + ohlc_jobs + ohlc_cronjobs
        print(f"\n   📊 Total OHLC collectors found: {len(all_ohlc)}")
        
        return {
            'deployments': ohlc_deployments,
            'jobs': ohlc_jobs, 
            'cronjobs': ohlc_cronjobs
        }
        
    except Exception as e:
        print(f"❌ Error finding collectors: {e}")
        return None

def analyze_collector_configs(collectors):
    """Analyze each collector's configuration to determine the best one"""
    
    print(f"\n2. ANALYZING COLLECTOR CONFIGURATIONS:")
    print("-" * 40)
    
    collector_analysis = {}
    
    # Analyze deployments
    for deployment in collectors['deployments']:
        print(f"\n📋 DEPLOYMENT: {deployment}")
        print("-" * 25)
        
        try:
            cmd = f"kubectl get deployment {deployment} -n crypto-collectors -o yaml"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                config = yaml.safe_load(result.stdout)
                
                # Extract key information
                spec = config.get('spec', {}).get('template', {}).get('spec', {})
                containers = spec.get('containers', [])
                
                if containers:
                    container = containers[0]
                    env_vars = {env.get('name'): env.get('value') for env in container.get('env', [])}
                    
                    analysis = {
                        'type': 'deployment',
                        'image': container.get('image', 'unknown'),
                        'env_vars': env_vars,
                        'replicas': config.get('spec', {}).get('replicas', 0),
                        'resources': container.get('resources', {}),
                        'table_target': env_vars.get('CRYPTO_PRICES_TABLE', 'unknown')
                    }
                    
                    print(f"   Image: {analysis['image']}")
                    print(f"   Replicas: {analysis['replicas']}")
                    print(f"   Target Table: {analysis['table_target']}")
                    print(f"   Key Env Vars: {len(analysis['env_vars'])}")
                    
                    # Check for comprehensive features
                    comprehensive_score = 0
                    if 'unified' in deployment.lower():
                        comprehensive_score += 3
                    if 'comprehensive' in deployment.lower():
                        comprehensive_score += 4
                    if 'premium' in deployment.lower():
                        comprehensive_score += 2
                    if analysis['table_target'] == 'ohlc_data':
                        comprehensive_score += 5
                    if analysis['replicas'] > 0:
                        comprehensive_score += 1
                    
                    analysis['comprehensive_score'] = comprehensive_score
                    print(f"   Comprehensive Score: {comprehensive_score}/10")
                    
                    collector_analysis[deployment] = analysis
                    
        except Exception as e:
            print(f"   ❌ Error analyzing {deployment}: {e}")
    
    # Analyze cronjobs
    for cronjob in collectors['cronjobs']:
        print(f"\n🕐 CRONJOB: {cronjob}")
        print("-" * 20)
        
        try:
            cmd = f"kubectl get cronjob {cronjob} -n crypto-collectors -o yaml"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                config = yaml.safe_load(result.stdout)
                
                # Extract key information
                job_spec = config.get('spec', {}).get('jobTemplate', {}).get('spec', {}).get('template', {}).get('spec', {})
                containers = job_spec.get('containers', [])
                
                if containers:
                    container = containers[0]
                    env_vars = {env.get('name'): env.get('value') for env in container.get('env', [])}
                    
                    analysis = {
                        'type': 'cronjob',
                        'image': container.get('image', 'unknown'),
                        'env_vars': env_vars,
                        'schedule': config.get('spec', {}).get('schedule', 'unknown'),
                        'table_target': env_vars.get('CRYPTO_PRICES_TABLE', 'unknown')
                    }
                    
                    print(f"   Image: {analysis['image']}")
                    print(f"   Schedule: {analysis['schedule']}")
                    print(f"   Target Table: {analysis['table_target']}")
                    
                    # Score cronjobs lower since they're batch
                    comprehensive_score = 1
                    if 'comprehensive' in cronjob.lower():
                        comprehensive_score += 2
                    if analysis['table_target'] == 'ohlc_data':
                        comprehensive_score += 3
                    
                    analysis['comprehensive_score'] = comprehensive_score
                    print(f"   Comprehensive Score: {comprehensive_score}/6")
                    
                    collector_analysis[cronjob] = analysis
                    
        except Exception as e:
            print(f"   ❌ Error analyzing {cronjob}: {e}")
    
    return collector_analysis

def recommend_best_collector(analysis):
    """Recommend which collector to keep based on analysis"""
    
    print(f"\n3. RECOMMENDATION:")
    print("-" * 20)
    
    if not analysis:
        print("❌ No collectors analyzed")
        return None
    
    # Sort by comprehensive score
    sorted_collectors = sorted(analysis.items(), key=lambda x: x[1].get('comprehensive_score', 0), reverse=True)
    
    print("📊 COLLECTOR RANKING:")
    for i, (name, info) in enumerate(sorted_collectors, 1):
        score = info.get('comprehensive_score', 0)
        table = info.get('table_target', 'unknown')
        type_info = info.get('type', 'unknown')
        print(f"   {i}. {name} | Score: {score} | Type: {type_info} | Table: {table}")
    
    # Recommend the best one
    best_collector = sorted_collectors[0]
    best_name = best_collector[0]
    best_info = best_collector[1]
    
    print(f"\n🏆 RECOMMENDED KEEPER:")
    print(f"   Name: {best_name}")
    print(f"   Score: {best_info.get('comprehensive_score', 0)}")
    print(f"   Type: {best_info.get('type', 'unknown')}")
    print(f"   Target: {best_info.get('table_target', 'unknown')}")
    
    # List others to archive
    others = [name for name, _ in sorted_collectors[1:]]
    if others:
        print(f"\n🗂️  TO ARCHIVE:")
        for other in others:
            print(f"   - {other}")
    
    return best_name, others

def create_archive_plan(keeper, to_archive):
    """Create detailed plan for archiving collectors"""
    
    print(f"\n4. ARCHIVE EXECUTION PLAN:")
    print("-" * 35)
    
    if not to_archive:
        print("✅ No collectors need archiving")
        return
    
    print(f"🏆 KEEPING: {keeper}")
    print(f"🗂️  ARCHIVING: {len(to_archive)} collectors")
    
    # Create backup commands
    backup_commands = []
    archive_commands = []
    
    for collector in to_archive:
        # Backup command
        backup_cmd = f"kubectl get deployment,cronjob,job {collector} -n crypto-collectors -o yaml > {collector}-backup.yaml"
        backup_commands.append(backup_cmd)
        
        # Archive command (scale to 0 for deployments, suspend for cronjobs)
        if 'deployment' in collector or any(word in collector.lower() for word in ['unified', 'comprehensive', 'premium']):
            # Assume it's a deployment if it has these keywords
            archive_cmd = f"kubectl scale deployment {collector} -n crypto-collectors --replicas=0"
        else:
            # Assume it's a cronjob
            archive_cmd = f"kubectl patch cronjob {collector} -n crypto-collectors -p '{{\"spec\":{{\"suspend\":true}}}}'"
        
        archive_commands.append(archive_cmd)
    
    print(f"\n📋 BACKUP COMMANDS:")
    for cmd in backup_commands:
        print(f"   {cmd}")
    
    print(f"\n🗂️  ARCHIVE COMMANDS:")
    for cmd in archive_commands:
        print(f"   {cmd}")
    
    # Create script file
    script_content = "#!/bin/bash\n"
    script_content += "# OHLC Collectors Archive Script\n"
    script_content += f"# Generated on: $(date)\n"
    script_content += f"# Keeping: {keeper}\n"
    script_content += f"# Archiving: {', '.join(to_archive)}\n\n"
    
    script_content += "echo '🗂️  Backing up OHLC collectors...'\n"
    for cmd in backup_commands:
        script_content += f"{cmd}\n"
    
    script_content += "\necho '📦 Archiving OHLC collectors...'\n"
    for cmd in archive_commands:
        script_content += f"{cmd}\n"
    
    script_content += f"\necho '✅ Archive complete! Keeping: {keeper}'\n"
    
    with open('archive_ohlc_collectors.sh', 'w') as f:
        f.write(script_content)
    
    print(f"\n📄 Created: archive_ohlc_collectors.sh")
    print("   Run this script to execute the archive plan")

if __name__ == "__main__":
    print("🎯 OHLC COLLECTORS CONSOLIDATION")
    print("=" * 50)
    
    # Step 1: Find all OHLC collectors
    collectors = audit_ohlc_collectors()
    
    if collectors:
        # Step 2: Analyze configurations
        analysis = analyze_collector_configs(collectors)
        
        # Step 3: Recommend best collector
        if analysis:
            keeper, to_archive = recommend_best_collector(analysis)
            
            # Step 4: Create archive plan
            create_archive_plan(keeper, to_archive)
            
            print(f"\n✨ OHLC Consolidation Analysis Complete!")
            print("🎯 Review the plan and run archive_ohlc_collectors.sh when ready")
        else:
            print("❌ No collector configurations could be analyzed")
    else:
        print("❌ No OHLC collectors found")