#!/usr/bin/env python3
"""
PRODUCTION PIPELINE - FAANG-Grade DevOps Approach
Connects training → predictions → dashboard in one seamless flow
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import time

class ProductionPipeline:
    """Unified production pipeline"""
    
    def __init__(self):
        self.log_file = Path('logs/pipeline.log')
        self.log_file.parent.mkdir(exist_ok=True)
    
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}\n"
        print(log_msg.strip())
        with open(self.log_file, 'a') as f:
            f.write(log_msg)
    
    def run_step(self, name, command, required=True):
        """Run a pipeline step"""
        self.log(f"▶️  Starting: {name}")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                self.log(f"✅ Completed: {name} ({elapsed:.1f}s)")
                if result.stdout:
                    # Log important output
                    for line in result.stdout.split('\n'):
                        if any(keyword in line.lower() for keyword in ['error', 'warning', 'accuracy', 'confidence', 'generated']):
                            self.log(f"   {line}")
                return True
            else:
                self.log(f"❌ Failed: {name}")
                if result.stderr:
                    self.log(f"   Error: {result.stderr[:500]}")
                if required:
                    raise Exception(f"{name} failed")
                return False
                
        except Exception as e:
            elapsed = time.time() - start_time
            self.log(f"❌ Exception in {name}: {e} ({elapsed:.1f}s)")
            if required:
                raise
            return False
    
    def check_models_exist(self):
        """Check if models are trained"""
        model_files = [
            'models/catboost_model.pkl',
            'models/features.pkl'
        ]
        
        all_exist = all(Path(f).exists() for f in model_files)
        
        if not all_exist:
            self.log("⚠️  Models not found. Training required.")
            return False
        
        self.log("✅ Models found")
        return True
    
    def run_full_pipeline(self, train_if_needed=True):
        """Run the complete production pipeline"""
        
        self.log("="*80)
        self.log("🚀 STARTING PRODUCTION PIPELINE")
        self.log("="*80)
        
        # Step 1: Check/ Train models
        if not self.check_models_exist():
            if train_if_needed:
                self.log("📊 Training models...")
                self.run_step(
                    "Model Training",
                    f"{sys.executable} enhanced_2.py --train --years 2023,2024 --no-tune",
                    required=True
                )
            else:
                raise Exception("Models not found and training disabled")
        
        # Step 2: Generate NFL predictions
        self.run_step(
            "NFL Predictions",
            f"{sys.executable} predict_today.py",
            required=True
        )
        
        # Step 3: Generate NBA predictions
        self.run_step(
            "NBA Predictions",
            f"{sys.executable} nba_predictions.py",
            required=False  # NBA is optional
        )
        
        # Step 4: Combine predictions
        self.run_step(
            "Combine Predictions",
            f"{sys.executable} generate_all_predictions.py",
            required=True
        )
        
        # Step 5: Create dashboard (Apple-grade)
        self.run_step(
            "Create Dashboard",
            f"{sys.executable} create_apple_dashboard.py",
            required=True
        )
        
        # Step 6: Collect actual results (Month 1: Continuous Learning)
        self.run_step(
            "Collect Actual Results",
            f"{sys.executable} continuous_learning.py --collect",
            required=False
        )
        
        # Step 6: Validate output
        self.validate_output()
        
        self.log("="*80)
        self.log("✅ PRODUCTION PIPELINE COMPLETE")
        self.log("="*80)
        
        # Print summary
        self.print_summary()
    
    def validate_output(self):
        """Validate pipeline output"""
        self.log("🔍 Validating output...")
        
        checks = {
            'Dashboard exists': Path('predictions/dashboard.html').exists(),
            'Predictions JSON exists': Path('predictions/all_predictions.json').exists(),
        }
        
        all_pass = True
        for check, passed in checks.items():
            if passed:
                self.log(f"   ✅ {check}")
            else:
                self.log(f"   ❌ {check}")
                all_pass = False
        
        if not all_pass:
            raise Exception("Validation failed")
    
    def print_summary(self):
        """Print pipeline summary"""
        try:
            with open('predictions/all_predictions.json', 'r') as f:
                data = json.load(f)
            
            nfl_count = len(data.get('nfl', []))
            nba_count = len(data.get('nba', []))
            total = nfl_count + nba_count
            
            high_conf = sum(1 for p in data.get('nfl', []) + data.get('nba', []) 
                          if p.get('is_high_confidence') or p.get('confidence_score', 0) > 0.7)
            
            self.log("\n📊 PIPELINE SUMMARY")
            self.log(f"   NFL Predictions: {nfl_count}")
            self.log(f"   NBA Predictions: {nba_count}")
            self.log(f"   Total: {total}")
            self.log(f"   High Confidence: {high_conf}")
            self.log(f"\n📄 Dashboard: predictions/dashboard.html")
            
        except Exception as e:
            self.log(f"   ⚠️  Could not generate summary: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Pipeline')
    parser.add_argument('--skip-training', action='store_true', 
                       help='Skip training if models exist')
    parser.add_argument('--train-only', action='store_true',
                       help='Only train models, skip predictions')
    
    args = parser.parse_args()
    
    pipeline = ProductionPipeline()
    
    if args.train_only:
        pipeline.run_step(
            "Model Training",
            f"{sys.executable} enhanced_2.py --train --years 2023,2024",
            required=True
        )
    else:
        pipeline.run_full_pipeline(train_if_needed=not args.skip_training)

if __name__ == '__main__':
    main()

