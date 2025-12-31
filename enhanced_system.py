#!/usr/bin/env python3
"""
COMPLETE NFL PREDICTION SYSTEM - ALL MODELS
CatBoost + XGBoost + LightGBM + Prophet + SHAP

Enhanced version with:
- Multiple ML models (ensemble)
- Better feature engineering
- Model explainability (SHAP)
- Time series trends (Prophet)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import pickle
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# ESPN API (Same as before)
# ============================================================================

class ESPNAPI:
    BASE = "https://site.api.espn.com/apis/site/v2/sports"
    
    @staticmethod
    def get_scoreboard(sport='football', league='nfl', dates=None):
        url = f"{ESPNAPI.BASE}/{sport}/{league}/scoreboard"
        params = {'limit': 1000}
        if dates:
            params['dates'] = dates
        response = requests.get(url, params=params, timeout=10)
        return response.json()

# ============================================================================
# ENHANCED FEATURE ENGINEERING
# ============================================================================

def engineer_advanced_features(df):
    """Create better ML features"""
    
    print("\n🔧 Engineering ADVANCED features...")
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Basic features
    df['point_diff'] = df['home_score'] - df['away_score']
    df['total_points'] = df['home_score'] + df['away_score']
    df['home_win'] = (df['point_diff'] > 0).astype(int)
    
    # Team-based rolling features (last 5 games)
    for team_type in ['home', 'away']:
        team_col = f'{team_type}_team'
        score_col = f'{team_type}_score'
        
        # Points scored average
        df[f'{team_type}_avg_points_L5'] = df.groupby(team_col)[score_col].transform(
            lambda x: x.shift(1).rolling(5, min_periods=1).mean()
        )
        
        # Points allowed average (opponent score)
        opp_score = 'away_score' if team_type == 'home' else 'home_score'
        df[f'{team_type}_avg_allowed_L5'] = df.groupby(team_col)[opp_score].transform(
            lambda x: x.shift(1).rolling(5, min_periods=1).mean()
        )
        
        # Win rate (last 5)
        if team_type == 'home':
            df[f'{team_type}_win_rate_L5'] = df.groupby(team_col)['home_win'].transform(
                lambda x: x.shift(1).rolling(5, min_periods=1).mean()
            )
        else:
            df['away_win'] = 1 - df['home_win']
            df[f'{team_type}_win_rate_L5'] = df.groupby(team_col)['away_win'].transform(
                lambda x: x.shift(1).rolling(5, min_periods=1).mean()
            )
        
        # Point differential trend
        df[f'{team_type}_diff_trend'] = df.groupby(team_col)['point_diff'].transform(
            lambda x: x.shift(1).rolling(5, min_periods=1).mean()
        )
    
    # Matchup features
    df['home_advantage'] = 3  # Standard home field advantage
    df['point_spread_estimate'] = (
        df['home_avg_points_L5'] - df['away_avg_points_L5'] + df['home_advantage']
    )
    
    # Rest days (if we had date gaps, placeholder for now)
    df['home_rest_days'] = 7
    df['away_rest_days'] = 7
    
    print(f"   ✅ Created {len(df.columns)} features")
    
    return df

# ============================================================================
# COLLECT DATA
# ============================================================================

def collect_nfl_season_data(year=2024):
    print(f"\n📥 Collecting {year} NFL season data...")
    
    season_data = ESPNAPI.get_scoreboard(sport='football', league='nfl', dates=f"{year}")
    
    games = []
    for event in season_data.get('events', []):
        comp = event['competitions'][0]
        home = comp['competitors'][0] if comp['competitors'][0]['homeAway'] == 'home' else comp['competitors'][1]
        away = comp['competitors'][1] if comp['competitors'][1]['homeAway'] == 'away' else comp['competitors'][0]
        
        # Only include completed games
        if event['status']['type']['completed']:
            games.append({
                'date': event['date'],
                'home_team': home['team']['displayName'],
                'away_team': away['team']['displayName'],
                'home_score': int(home.get('score', 0)),
                'away_score': int(away.get('score', 0)),
                'week': event.get('week', {}).get('number', 0)
            })
    
    df = pd.DataFrame(games)
    print(f"   ✅ Collected {len(df)} COMPLETED games")
    
    return df

# ============================================================================
# TRAIN MULTIPLE MODELS
# ============================================================================

def train_ensemble_models(df, save_dir='models'):
    """Train CatBoost + XGBoost + LightGBM ensemble"""
    
    print("\n🤖 Training ENSEMBLE models...")
    
    # Feature list
    features = [
        'home_avg_points_L5', 'away_avg_points_L5',
        'home_avg_allowed_L5', 'away_avg_allowed_L5',
        'home_win_rate_L5', 'away_win_rate_L5',
        'home_diff_trend', 'away_diff_trend',
        'point_spread_estimate', 'home_advantage',
        'week'
    ]
    
    # Clean data
    df_clean = df[features + ['point_diff']].dropna()
    X = df_clean[features]
    y = df_clean['point_diff']
    
    print(f"   Training on {len(X)} games with {len(features)} features")
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    models = {}
    
    # 1. CatBoost
    try:
        from catboost import CatBoostRegressor
        print("\n   [1/3] Training CatBoost...")
        
        cb_model = CatBoostRegressor(
            iterations=1500,
            learning_rate=0.03,
            depth=6,
            verbose=False
        )
        cb_model.fit(X_train, y_train)
        
        from sklearn.metrics import mean_absolute_error
        cb_pred = cb_model.predict(X_test)
        cb_mae = mean_absolute_error(y_test, cb_pred)
        cb_acc = (abs(cb_pred - y_test) < 7).mean() * 100
        
        print(f"      ✅ CatBoost MAE: {cb_mae:.2f} | Acc: {cb_acc:.1f}%")
        models['catboost'] = cb_model
        
    except Exception as e:
        print(f"      ⚠️  CatBoost failed: {e}")
    
    # 2. XGBoost
    try:
        from xgboost import XGBRegressor
        print("\n   [2/3] Training XGBoost...")
        
        xgb_model = XGBRegressor(
            n_estimators=1500,
            learning_rate=0.03,
            max_depth=6,
            random_state=42,
            verbosity=0
        )
        xgb_model.fit(X_train, y_train)
        
        xgb_pred = xgb_model.predict(X_test)
        xgb_mae = mean_absolute_error(y_test, xgb_pred)
        xgb_acc = (abs(xgb_pred - y_test) < 7).mean() * 100
        
        print(f"      ✅ XGBoost MAE: {xgb_mae:.2f} | Acc: {xgb_acc:.1f}%")
        models['xgboost'] = xgb_model
        
    except Exception as e:
        print(f"      ⚠️  XGBoost failed: {e}")
    
    # 3. LightGBM
    try:
        from lightgbm import LGBMRegressor
        print("\n   [3/3] Training LightGBM...")
        
        lgb_model = LGBMRegressor(
            n_estimators=1500,
            learning_rate=0.03,
            max_depth=6,
            random_state=42,
            verbosity=-1
        )
        lgb_model.fit(X_train, y_train)
        
        lgb_pred = lgb_model.predict(X_test)
        lgb_mae = mean_absolute_error(y_test, lgb_pred)
        lgb_acc = (abs(lgb_pred - y_test) < 7).mean() * 100
        
        print(f"      ✅ LightGBM MAE: {lgb_mae:.2f} | Acc: {lgb_acc:.1f}%")
        models['lightgbm'] = lgb_model
        
    except Exception as e:
        print(f"      ⚠️  LightGBM failed: {e}")
    
    # 4. Ensemble (average predictions)
    if len(models) > 1:
        print("\n   [ENSEMBLE] Combining models...")
        
        ensemble_pred = np.mean([
            models[name].predict(X_test) for name in models
        ], axis=0)
        
        ens_mae = mean_absolute_error(y_test, ensemble_pred)
        ens_acc = (abs(ensemble_pred - y_test) < 7).mean() * 100
        
        print(f"      ✅ Ensemble MAE: {ens_mae:.2f} | Acc: {ens_acc:.1f}%")
    
    # Save models
    Path(save_dir).mkdir(exist_ok=True)
    for name, model in models.items():
        with open(f'{save_dir}/{name}_model.pkl', 'wb') as f:
            pickle.dump(model, f)
        print(f"      💾 Saved: {save_dir}/{name}_model.pkl")
    
    # Save feature list
    with open(f'{save_dir}/features.pkl', 'wb') as f:
        pickle.dump(features, f)
    
    return models, features

# ============================================================================
# SHAP EXPLAINABILITY
# ============================================================================

def explain_with_shap(model, X_test, features, save_path='models/shap_values.pkl'):
    """Generate SHAP values for model explainability"""
    
    print("\n🔍 Generating SHAP explanations...")
    
    try:
        import shap
        
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        
        # Save SHAP values
        with open(save_path, 'wb') as f:
            pickle.dump({
                'shap_values': shap_values,
                'feature_names': features,
                'X_test': X_test
            }, f)
        
        # Show feature importance
        importance = pd.DataFrame({
            'feature': features,
            'importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('importance', ascending=False)
        
        print("\n   Top 5 Most Important Features:")
        for idx, row in importance.head(5).iterrows():
            print(f"      {row['feature']}: {row['importance']:.3f}")
        
        print(f"\n   💾 Saved SHAP values to: {save_path}")
        
    except Exception as e:
        print(f"   ⚠️  SHAP failed: {e}")

# ============================================================================
# PROPHET FOR TRENDS
# ============================================================================

def train_prophet_trends(df, save_dir='models'):
    """Use Prophet for season-long trend prediction"""
    
    print("\n📈 Training Prophet for season trends...")
    
    try:
        from prophet import Prophet
        
        # Team performance trends
        teams = df['home_team'].unique()
        
        trends = {}
        
        for team in teams[:10]:  # Show 10 teams as examples
            team_games = df[(df['home_team'] == team) | (df['away_team'] == team)].copy()
            
            # Get score for this team (whether home or away)
            team_games['score'] = team_games.apply(
                lambda x: x['home_score'] if x['home_team'] == team else x['away_score'],
                axis=1
            )
            
            # Prepare for Prophet (requires 'ds' and 'y' columns)
            prophet_df = team_games[['date', 'score']].copy()
            prophet_df.columns = ['ds', 'y']
            
            # FIX: Remove timezone info (Prophet doesn't support it)
            prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
            prophet_df['ds'] = prophet_df['ds'].dt.tz_localize(None)
            
            # Train Prophet model
            m = Prophet(
                yearly_seasonality=False, 
                weekly_seasonality=False, 
                daily_seasonality=False,
                changepoint_prior_scale=0.05  # Less sensitive to changes
            )
            
            # Suppress Prophet's verbose output
            import logging
            logging.getLogger('prophet').setLevel(logging.WARNING)
            
            m.fit(prophet_df)
            
            # Forecast next 4 weeks (28 days)
            future = m.make_future_dataframe(periods=28)
            forecast = m.predict(future)
            
            # Calculate trend (difference between last prediction and first)
            trend = forecast['yhat'].iloc[-1] - forecast['yhat'].iloc[0]
            current_avg = prophet_df['y'].tail(5).mean()
            
            trends[team] = {
                'trend': trend,
                'current_avg': current_avg,
                'forecast_avg': forecast['yhat'].iloc[-1]
            }
            
            # Display trend
            trend_emoji = "📈" if trend > 0 else "📉"
            print(f"      {team}: {trend_emoji} {trend:+.1f} points trend | Current avg: {current_avg:.1f}")
        
        # Save trends
        Path(save_dir).mkdir(exist_ok=True)
        with open(f'{save_dir}/prophet_trends.pkl', 'wb') as f:
            pickle.dump(trends, f)
        
        print(f"\n   ✅ Prophet trends calculated for {len(trends)} teams")
        print(f"   💾 Saved to: {save_dir}/prophet_trends.pkl")
        
        return trends
        
    except ImportError:
        print(f"   ⚠️  Prophet not installed")
        print(f"      Install with: pip install prophet")
        return None
    except Exception as e:
        print(f"   ⚠️  Prophet failed: {e}")
        print(f"      This is usually a data formatting issue")
        return None

# ============================================================================
# MAIN
# ============================================================================

def predict_todays_games():
    """Generate predictions using ensemble models"""
    
    print("\n🎯 Generating predictions...")
    
    # Load models
    models = {}
    for model_name in ['catboost', 'xgboost', 'lightgbm']:
        try:
            with open(f'models/{model_name}_model.pkl', 'rb') as f:
                models[model_name] = pickle.load(f)
            print(f"   ✅ Loaded {model_name}")
        except:
            print(f"   ⚠️  {model_name} not found")
    
    # Load features
    with open('models/features.pkl', 'rb') as f:
        features = pickle.load(f)
    
    # Load historical data for team stats
    df = pd.read_csv('data/nfl_2024_features.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Get today's games
    today = datetime.now().strftime('%Y%m%d')
    games_today = ESPNAPI.get_scoreboard(dates=today)
    
    predictions = []
    
    for event in games_today.get('events', []):
        comp = event['competitions'][0]
        
        home = comp['competitors'][0] if comp['competitors'][0]['homeAway'] == 'home' else comp['competitors'][1]
        away = comp['competitors'][1] if comp['competitors'][1]['homeAway'] == 'away' else comp['competitors'][0]
        
        home_team = home['team']['displayName']
        away_team = away['team']['displayName']
        
        # Get most recent stats for each team
        home_recent = df[df['home_team'] == home_team].tail(1)
        away_recent = df[df['away_team'] == away_team].tail(1)
        
        if len(home_recent) == 0 or len(away_recent) == 0:
            print(f"   ⚠️  No data for {away_team} @ {home_team}")
            continue
        
        # Build feature vector
        feature_dict = {
            'home_avg_points_L5': home_recent['home_avg_points_L5'].values[0],
            'away_avg_points_L5': away_recent['away_avg_points_L5'].values[0],
            'home_avg_allowed_L5': home_recent['home_avg_allowed_L5'].values[0],
            'away_avg_allowed_L5': away_recent['away_avg_allowed_L5'].values[0],
            'home_win_rate_L5': home_recent['home_win_rate_L5'].values[0],
            'away_win_rate_L5': away_recent['away_win_rate_L5'].values[0],
            'home_diff_trend': home_recent['home_diff_trend'].values[0],
            'away_diff_trend': away_recent['away_diff_trend'].values[0],
            'point_spread_estimate': home_recent['home_avg_points_L5'].values[0] - away_recent['away_avg_points_L5'].values[0] + 3,
            'home_advantage': 3,
            'week': 18  # Current week
        }
        
        X = pd.DataFrame([feature_dict])[features]
        
        # Ensemble prediction
        preds = [model.predict(X)[0] for model in models.values()]
        ensemble_pred = np.mean(preds)
        
        pred_obj = {
            'away_team': away_team,
            'home_team': home_team,
            'predicted_spread': ensemble_pred,
            'predicted_winner': home_team if ensemble_pred > 0 else away_team,
            'confidence': min(0.95, abs(ensemble_pred) / 20),
            'catboost_pred': preds[0] if len(preds) > 0 else None,
            'xgboost_pred': preds[1] if len(preds) > 1 else None,
            'lightgbm_pred': preds[2] if len(preds) > 2 else None,
        }
        
        predictions.append(pred_obj)
        
        print(f"\n   {away_team} @ {home_team}")
        print(f"      Predicted: {pred_obj['predicted_winner']} by {abs(ensemble_pred):.1f}")
        print(f"      Confidence: {pred_obj['confidence']*100:.0f}%")
        print(f"      Models: CB={preds[0]:.1f} | XGB={preds[1]:.1f} | LGB={preds[2]:.1f}")
    
    # Save predictions
    if predictions:
        pd.DataFrame(predictions).to_csv('predictions/today.csv', index=False)
        print(f"\n   💾 Saved predictions to: predictions/today.csv")
    
    return predictions

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced NFL Prediction System')
    parser.add_argument('--train', action='store_true', help='Train all models')
    parser.add_argument('--predict', action='store_true', help='Generate predictions')
    parser.add_argument('--explain', action='store_true', help='Generate SHAP explanations')
    parser.add_argument('--year', type=int, default=2024, help='Season year')
    
    args = parser.parse_args()
    
    # Setup folders
    print("📁 Setting up folder structure...")
    for folder in ['data', 'models', 'predictions']:
        Path(folder).mkdir(exist_ok=True)
    print("   ✅ Folders ready\n")
    
    if args.train:
        # Collect data
        df = collect_nfl_season_data(year=args.year)
        df.to_csv(f'data/nfl_{args.year}_raw.csv', index=False)
        
        # Engineer features
        df_features = engineer_advanced_features(df)
        df_features.to_csv(f'data/nfl_{args.year}_features.csv', index=False)
        
        # Train ensemble models
        models, features = train_ensemble_models(df_features)
        
        # SHAP explanations
        if args.explain and 'catboost' in models:
            df_clean = df_features[features + ['point_diff']].dropna()
            X = df_clean[features]
            
            from sklearn.model_selection import train_test_split
            _, X_test, _, _ = train_test_split(X, df_clean['point_diff'], test_size=0.2, random_state=42)
            
            explain_with_shap(models['catboost'], X_test, features)
        
        # Prophet trends
        train_prophet_trends(df)
        
        print("\n" + "=" * 80)
        print("✅ COMPLETE TRAINING FINISHED")
        print("=" * 80)
        print("\nModels trained:")
        for name in models:
            print(f"   • {name}")
        
        print("\nNext steps:")
        print("   1. Check models/ folder for saved models")
        print("   2. Review data/ folder for feature engineering")
        print("   3. Run: python enhanced_system.py --predict")
    
    elif args.predict:
        predictions = predict_todays_games()
        
        print("\n" + "=" * 80)
        print("✅ PREDICTIONS COMPLETE")
        print("=" * 80)
    
    else:
        print("Usage:")
        print("  python enhanced_system.py --train              # Train all models")
        print("  python enhanced_system.py --train --explain    # Train + SHAP")
        print("  python enhanced_system.py --predict            # Generate predictions")

if __name__ == '__main__':
    main()