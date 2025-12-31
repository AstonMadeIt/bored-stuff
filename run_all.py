#!/usr/bin/env python3
"""
Master script: Generate all predictions and create dashboard
Run this to get everything in one go!
Now uses production pipeline for reliability
"""

from production_pipeline import ProductionPipeline
from pathlib import Path

def main():
    pipeline = ProductionPipeline()
    
    # Use production pipeline (skips training if models exist)
    pipeline.run_full_pipeline(train_if_needed=False)
    
    # Success!
    dashboard_path = Path(__file__).parent / 'predictions' / 'dashboard.html'
    print("\n" + "="*80)
    print("✅ SUCCESS!")
    print("="*80)
    print(f"\n📊 Dashboard created: {dashboard_path}")
    print(f"   Open in browser: file://{dashboard_path.absolute()}")
    print("\n💡 Tip: Use 'python3 production_pipeline.py' for full training + predictions")

if __name__ == '__main__':
    main()

