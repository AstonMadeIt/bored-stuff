#!/usr/bin/env python3
"""
Test Full Pipeline - Verify All Connections
Tests that ONE command connects: APIs → Models → Predictions → Dashboard
"""

import sys
from pathlib import Path
import json

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    tests = {
        'ESPN API': False,
        'Vegas Odds API': False,
        'NBA API': False,
        'nfl_data_py': False,
        'API Integration': False,
        'CatBoost': False,
        'XGBoost': False,
        'LightGBM': False,
        'Optuna': False,
        'SHAP': False,
    }
    
    # Test ESPN API
    try:
        from enhanced_system_fixed import ESPNAPI
        tests['ESPN API'] = True
    except:
        pass
    
    # Test Vegas Odds API
    try:
        from enhanced_system_fixed import VegasOddsAPI
        tests['Vegas Odds API'] = True
    except:
        pass
    
    # Test NBA API
    try:
        from nba_api.stats.endpoints import scoreboardv2
        tests['NBA API'] = True
    except:
        pass
    
    # Test nfl_data_py
    try:
        import nfl_data_py as nfl
        tests['nfl_data_py'] = True
    except:
        pass
    
    # Test API Integration
    try:
        from integrate_apis import enhance_features_with_apis
        tests['API Integration'] = True
    except:
        pass
    
    # Test Models
    try:
        import catboost
        tests['CatBoost'] = True
    except:
        pass
    
    try:
        import xgboost
        tests['XGBoost'] = True
    except:
        pass
    
    try:
        import lightgbm
        tests['LightGBM'] = True
    except:
        pass
    
    try:
        import optuna
        tests['Optuna'] = True
    except:
        pass
    
    try:
        import shap
        tests['SHAP'] = True
    except:
        pass
    
    # Print results
    all_pass = True
    for name, passed in tests.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
        if not passed:
            all_pass = False
    
    return all_pass

def test_connections():
    """Test that scripts are connected"""
    print("\n🔗 Testing connections...")
    
    connections = {
        'production_pipeline.py exists': Path('production_pipeline.py').exists(),
        'predict_today.py exists': Path('predict_today.py').exists(),
        'nba_predictions.py exists': Path('nba_predictions.py').exists(),
        'create_nymag_dashboard.py exists': Path('create_nymag_dashboard.py').exists(),
        'integrate_apis.py exists': Path('integrate_apis.py').exists(),
    }
    
    # Check if API integration is imported in predict_today.py
    try:
        with open('predict_today.py', 'r') as f:
            content = f.read()
            connections['API integration in predict_today.py'] = 'enhance_features_with_apis' in content
    except:
        connections['API integration in predict_today.py'] = False
    
    # Check if API integration is imported in nba_predictions.py
    try:
        with open('nba_predictions.py', 'r') as f:
            content = f.read()
            connections['API integration in nba_predictions.py'] = 'enhance_features_with_apis' in content
    except:
        connections['API integration in nba_predictions.py'] = False
    
    all_pass = True
    for name, passed in connections.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
        if not passed:
            all_pass = False
    
    return all_pass

def test_models_exist():
    """Test if models are trained"""
    print("\n🤖 Testing models...")
    
    models = {
        'CatBoost model': Path('models/catboost_model.pkl').exists(),
        'Features list': Path('models/features.pkl').exists(),
    }
    
    all_pass = True
    for name, exists in models.items():
        status = "✅" if exists else "⚠️  (not trained yet)"
        print(f"   {status} {name}")
        if not exists:
            all_pass = False
    
    return all_pass

def test_pipeline_flow():
    """Test that pipeline connects everything"""
    print("\n🔄 Testing pipeline flow...")
    
    # Check production_pipeline.py calls all components
    try:
        with open('production_pipeline.py', 'r') as f:
            content = f.read()
        
        checks = {
            'Calls enhanced_2.py (training)': 'enhanced_2.py' in content,
            'Calls predict_today.py (NFL)': 'predict_today.py' in content,
            'Calls nba_predictions.py (NBA)': 'nba_predictions.py' in content,
            'Calls generate_all_predictions.py': 'generate_all_predictions.py' in content,
            'Calls create_nymag_dashboard.py': 'create_nymag_dashboard.py' in content,
        }
        
        all_pass = True
        for name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {name}")
            if not passed:
                all_pass = False
        
        return all_pass
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("="*80)
    print("🧪 FULL PIPELINE CONNECTION TEST")
    print("="*80)
    
    results = {
        'Imports': test_imports(),
        'Connections': test_connections(),
        'Models': test_models_exist(),
        'Pipeline Flow': test_pipeline_flow(),
    }
    
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    all_pass = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "⚠️  PARTIAL"
        print(f"{status}: {name}")
        if not passed and name != 'Models':  # Models can be missing
            all_pass = False
    
    print("\n" + "="*80)
    if all_pass:
        print("✅ ALL CONNECTIONS VERIFIED!")
        print("\n🚀 Run: python3 production_pipeline.py")
    else:
        print("⚠️  SOME CONNECTIONS MISSING")
        print("\n📝 See CONNECTION_STATUS.md for details")
    print("="*80)

if __name__ == '__main__':
    main()


