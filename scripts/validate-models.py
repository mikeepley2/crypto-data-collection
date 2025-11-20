#!/usr/bin/env python3
"""
ML Models Validation Script

This script validates that all required ML models are available in the persistent volume
and are properly configured for use by the crypto data collection services.

Usage:
    python validate-models.py
    
Environment Variables:
    MODEL_CACHE_DIR: Directory containing the ML models (default: /app/models)
    MODEL_SOURCE: Source of models (default: persistent_volume)
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ModelValidator:
    """Validates ML models in persistent volume"""
    
    def __init__(self, model_cache_dir: str = None):
        self.model_cache_dir = Path(model_cache_dir or os.getenv('MODEL_CACHE_DIR', '/app/models'))
        self.model_source = os.getenv('MODEL_SOURCE', 'persistent_volume')
        
        # Required models configuration
        self.required_models = {
            'finbert': {
                'description': 'Financial sentiment analysis model',
                'files': ['pytorch_model.bin', 'config.json', 'tokenizer.json'],
                'min_size_mb': 800,  # Minimum expected size in MB
                'max_size_mb': 2000  # Maximum expected size in MB
            },
            'cryptobert': {
                'description': 'Cryptocurrency sentiment analysis model',
                'files': ['pytorch_model.bin', 'config.json', 'tokenizer.json'],
                'min_size_mb': 800,
                'max_size_mb': 2000
            },
            'twitter-roberta': {
                'description': 'Twitter sentiment analysis model',
                'files': ['pytorch_model.bin', 'config.json', 'tokenizer.json'],
                'min_size_mb': 400,
                'max_size_mb': 800
            }
        }
        
        self.validation_results = {}
    
    def check_directory_exists(self) -> bool:
        """Check if model cache directory exists"""
        logger.info(f"🔍 Checking model directory: {self.model_cache_dir}")
        
        if not self.model_cache_dir.exists():
            logger.error(f"❌ Model directory not found: {self.model_cache_dir}")
            logger.info("💡 Ensure the persistent volume is mounted correctly")
            return False
        
        if not self.model_cache_dir.is_dir():
            logger.error(f"❌ Model cache path is not a directory: {self.model_cache_dir}")
            return False
        
        logger.info(f"✅ Model directory exists and is accessible")
        return True
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load and validate metadata file"""
        metadata_file = self.model_cache_dir / 'model-metadata.yaml'
        
        logger.info(f"🔍 Checking metadata file: {metadata_file}")
        
        if not metadata_file.exists():
            logger.warning(f"⚠️ Model metadata not found: {metadata_file}")
            logger.info("💡 This might indicate models haven't been initialized yet")
            logger.info("💡 Run the model setup job: kubectl apply -f k8s/k3s-production/model-setup-job.yaml")
            return {}
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = yaml.safe_load(f)
            
            logger.info("✅ Metadata file loaded successfully")
            
            # Log metadata summary
            if 'setup' in metadata:
                setup_info = metadata['setup']
                logger.info(f"📊 Last updated: {setup_info.get('last_updated', 'Unknown')}")
                logger.info(f"📊 Total size: {setup_info.get('total_size', 'Unknown')}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to load metadata: {e}")
            return {}
    
    def validate_model(self, model_name: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single model"""
        logger.info(f"🔍 Validating {model_name}...")
        
        model_path = self.model_cache_dir / model_name
        result = {
            'name': model_name,
            'exists': False,
            'files_valid': False,
            'size_valid': False,
            'errors': [],
            'warnings': [],
            'size_mb': 0
        }
        
        # Check if model directory exists
        if not model_path.exists():
            error = f"Model directory missing: {model_path}"
            result['errors'].append(error)
            logger.error(f"❌ {error}")
            return result
        
        result['exists'] = True
        
        # Check required files
        missing_files = []
        total_size = 0
        
        for required_file in model_config['files']:
            file_path = model_path / required_file
            if not file_path.exists():
                missing_files.append(required_file)
            else:
                try:
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    logger.debug(f"✅ {required_file}: {file_size / (1024**2):.1f}MB")
                except Exception as e:
                    result['warnings'].append(f"Could not stat {required_file}: {e}")
        
        if missing_files:
            error = f"Missing files: {missing_files}"
            result['errors'].append(error)
            logger.error(f"❌ {error}")
        else:
            result['files_valid'] = True
            logger.info(f"✅ All required files present for {model_name}")
        
        # Check model size
        total_size_mb = total_size / (1024**2)
        result['size_mb'] = round(total_size_mb, 1)
        
        min_size = model_config['min_size_mb']
        max_size = model_config['max_size_mb']
        
        if total_size_mb < min_size:
            warning = f"Model size ({total_size_mb:.1f}MB) is smaller than expected (>{min_size}MB)"
            result['warnings'].append(warning)
            logger.warning(f"⚠️ {warning}")
        elif total_size_mb > max_size:
            warning = f"Model size ({total_size_mb:.1f}MB) is larger than expected (<{max_size}MB)"
            result['warnings'].append(warning)
            logger.warning(f"⚠️ {warning}")
        else:
            result['size_valid'] = True
            logger.info(f"✅ Model size valid: {total_size_mb:.1f}MB")
        
        # Check permissions (if running as non-root)
        try:
            # Try to read the main model file
            main_model_file = model_path / 'pytorch_model.bin'
            if main_model_file.exists():
                with open(main_model_file, 'rb') as f:
                    f.read(1024)  # Read first 1KB to test access
                logger.debug(f"✅ Model file readable: {main_model_file}")
        except PermissionError:
            error = "Permission denied reading model files"
            result['errors'].append(error)
            logger.error(f"❌ {error}")
        except Exception as e:
            warning = f"Could not test file readability: {e}"
            result['warnings'].append(warning)
            logger.warning(f"⚠️ {warning}")
        
        return result
    
    def validate_all_models(self) -> Dict[str, Any]:
        """Validate all required models"""
        logger.info("🚀 Starting comprehensive model validation...")
        
        # Check directory
        if not self.check_directory_exists():
            return {
                'success': False,
                'error': 'Model directory not accessible',
                'models': {}
            }
        
        # Load metadata
        metadata = self.load_metadata()
        
        # Validate each model
        results = {}
        total_errors = 0
        total_warnings = 0
        
        for model_name, model_config in self.required_models.items():
            result = self.validate_model(model_name, model_config)
            results[model_name] = result
            
            total_errors += len(result['errors'])
            total_warnings += len(result['warnings'])
        
        # Summary
        valid_models = [name for name, result in results.items() 
                       if result['files_valid'] and len(result['errors']) == 0]
        
        total_size_gb = sum(result['size_mb'] for result in results.values()) / 1024
        
        summary = {
            'success': len(valid_models) == len(self.required_models),
            'valid_models': len(valid_models),
            'total_models': len(self.required_models),
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'total_size_gb': round(total_size_gb, 2),
            'models': results,
            'metadata': metadata
        }
        
        # Log summary
        logger.info("📊 Validation Summary:")
        logger.info(f"   Valid models: {len(valid_models)}/{len(self.required_models)}")
        logger.info(f"   Total size: {total_size_gb:.2f}GB")
        logger.info(f"   Errors: {total_errors}")
        logger.info(f"   Warnings: {total_warnings}")
        
        if summary['success']:
            logger.info("✅ All models validated successfully!")
        else:
            logger.error("❌ Model validation failed!")
            for model_name, result in results.items():
                if result['errors']:
                    logger.error(f"   {model_name}: {', '.join(result['errors'])}")
        
        return summary
    
    def wait_for_models(self, timeout_seconds: int = 300, check_interval: int = 10) -> bool:
        """Wait for models to become available"""
        logger.info(f"⏳ Waiting for models to become available (timeout: {timeout_seconds}s)...")
        
        start_time = time.time()
        attempts = 0
        
        while time.time() - start_time < timeout_seconds:
            attempts += 1
            logger.info(f"🔍 Validation attempt {attempts}...")
            
            result = self.validate_all_models()
            if result['success']:
                logger.info(f"✅ Models ready after {attempts} attempts ({time.time() - start_time:.1f}s)")
                return True
            
            if attempts == 1:
                # First attempt - show what we're waiting for
                logger.info("💡 Models not ready yet. Checking:")
                for model_name, model_result in result['models'].items():
                    if model_result['errors']:
                        logger.info(f"   ❌ {model_name}: {model_result['errors'][0]}")
                    else:
                        logger.info(f"   ✅ {model_name}: OK")
            
            logger.info(f"⏳ Waiting {check_interval}s before next check...")
            time.sleep(check_interval)
        
        logger.error(f"❌ Models not ready after {timeout_seconds}s timeout")
        return False
    
    def export_validation_report(self, output_file: str = None) -> str:
        """Export validation results to JSON file"""
        results = self.validate_all_models()
        
        if output_file is None:
            output_file = f"/tmp/model-validation-{int(time.time())}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"📄 Validation report exported: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"❌ Failed to export report: {e}")
            return ""

def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate ML models in persistent volume')
    parser.add_argument('--model-dir', type=str, help='Model cache directory')
    parser.add_argument('--wait', action='store_true', help='Wait for models to become available')
    parser.add_argument('--timeout', type=int, default=300, help='Wait timeout in seconds')
    parser.add_argument('--export-report', type=str, help='Export validation report to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Reduce logging output')
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Initialize validator
    validator = ModelValidator(args.model_dir)
    
    try:
        if args.wait:
            # Wait for models
            success = validator.wait_for_models(timeout_seconds=args.timeout)
        else:
            # Single validation
            result = validator.validate_all_models()
            success = result['success']
        
        # Export report if requested
        if args.export_report:
            validator.export_validation_report(args.export_report)
        
        # Exit with appropriate code
        if success:
            logger.info("✅ Model validation completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Model validation failed")
            logger.info("💡 Troubleshooting:")
            logger.info("   1. Check if model setup job completed: kubectl get job ml-models-setup -n crypto-data-collection")
            logger.info("   2. Check persistent volume: kubectl get pv ml-models-pv")
            logger.info("   3. Check volume mount: kubectl describe pod <pod-name> -n crypto-data-collection")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()