#!/usr/bin/env python3
"""
Generate predictions for both NFL and NBA games
Creates a beautiful HTML dashboard
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import database for tracking
try:
    from database import PredictionDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️  Database not available - predictions won't be tracked")

# Import prediction functions
try:
    from predict_today import predict_todays_games
    NFL_AVAILABLE = True
except ImportError:
    NFL_AVAILABLE = False
    print("⚠️  NFL predictions not available")

try:
    from nba_predictions import predict_nba_games
    NBA_AVAILABLE = True
except ImportError:
    NBA_AVAILABLE = False
    print("⚠️  NBA predictions not available")

def generate_all_predictions():
    """Generate predictions for both sports"""
    
    print("="*80)
    print("🏈🏀 GENERATING ALL PREDICTIONS")
    print("="*80)
    
    all_predictions = {
        'nfl': [],
        'nba': [],
        'generated_at': datetime.now().isoformat(),
        'nfl_count': 0,
        'nba_count': 0
    }
    
    # Generate NFL predictions
    if NFL_AVAILABLE:
        print("\n🏈 Generating NFL predictions...")
        try:
            nfl_preds = predict_todays_games()
            if not nfl_preds.empty:
                # Convert to dict format
                for _, pred in nfl_preds.iterrows():
                    pred_dict = pred.to_dict()
                    pred_dict['sport'] = 'NFL'
                    all_predictions['nfl'].append(pred_dict)
                all_predictions['nfl_count'] = len(all_predictions['nfl'])
                print(f"   ✅ Generated {all_predictions['nfl_count']} NFL predictions")
            else:
                print("   ⚠️  No NFL games today")
        except Exception as e:
            print(f"   ❌ Error generating NFL predictions: {e}")
    else:
        print("   ⚠️  NFL predictions not available")
    
    # Generate NBA predictions
    if NBA_AVAILABLE:
        print("\n🏀 Generating NBA predictions...")
        print("   🎯 Clutch Analyzer Formula: (Streak × Late Game) / (Record Divergence - PPG Divergence)")
        try:
            nba_preds = predict_nba_games()
            if not nba_preds.empty:
                # Convert to dict format
                for _, pred in nba_preds.iterrows():
                    pred_dict = pred.to_dict()
                    pred_dict['sport'] = 'NBA'
                    all_predictions['nba'].append(pred_dict)
                all_predictions['nba_count'] = len(all_predictions['nba'])
                print(f"   ✅ Generated {all_predictions['nba_count']} NBA predictions")
            else:
                print("   ⚠️  No NBA games today")
        except Exception as e:
            print(f"   ❌ Error generating NBA predictions: {e}")
    else:
        print("   ⚠️  NBA predictions not available")
    
    # Save JSON
    Path('predictions').mkdir(exist_ok=True)
    json_path = Path('predictions/all_predictions.json')
    with open(json_path, 'w') as f:
        json.dump(all_predictions, f, indent=2, default=str)
    
    # Save to database for tracking (Month 1: Continuous Learning)
    if DB_AVAILABLE:
        try:
            db = PredictionDB()
            saved_count = 0
            for pred in all_predictions['nfl'] + all_predictions['nba']:
                try:
                    db.save_prediction(pred)
                    saved_count += 1
                except Exception as e:
                    pass  # Skip duplicates
            print(f"   💾 Saved {saved_count} predictions to database for tracking")
        except Exception as e:
            print(f"   ⚠️  Database save failed: {e}")
    
    # Store in automated validation system
    try:
        from automated_validation_system import AutomatedValidationSystem
        validation_system = AutomatedValidationSystem()
        validation_count = validation_system.store_predictions(all_predictions['nfl'] + all_predictions['nba'])
        print(f"   ✅ Stored {validation_count} predictions in validation system")
    except ImportError:
        pass  # Validation system optional
    except Exception as e:
        print(f"   ⚠️  Validation system save failed: {e}")
    
    print(f"\n✅ Total predictions: {all_predictions['nfl_count']} NFL + {all_predictions['nba_count']} NBA")
    print(f"   Saved to: {json_path}")
    
    return all_predictions

if __name__ == '__main__':
    predictions = generate_all_predictions()
    print("\n🎉 All predictions generated!")

