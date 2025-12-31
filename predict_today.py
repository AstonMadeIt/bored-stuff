#!/usr/bin/env python3
"""
Predict Today's NFL Games
Fetches today's games and generates predictions with confidence tiers
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import sys
import json

# Import from the main system
sys.path.append(str(Path(__file__).parent))
from enhanced_system_fixed import (
    ESPNAPI, VegasOddsAPI, engineer_advanced_features, collect_nfl_season_data
)
from database import PredictionDB

# Import API integration for enhanced features
try:
    from integrate_apis import enhance_features_with_apis
    API_INTEGRATION_AVAILABLE = True
except ImportError:
    API_INTEGRATION_AVAILABLE = False
    print("⚠️  API integration module not found. Install nfl-data-py for enhanced features.")

def load_ensemble_models():
    """Load all trained ensemble models (CatBoost, XGBoost, LightGBM) and feature list"""
    models = {}
    try:
        # Load CatBoost (primary)
        with open('models/catboost_model.pkl', 'rb') as f:
            models['catboost'] = pickle.load(f)
        
        # Load XGBoost (if available)
        try:
            with open('models/xgboost_model.pkl', 'rb') as f:
                models['xgboost'] = pickle.load(f)
        except FileNotFoundError:
            pass
        
        # Load LightGBM (if available)
        try:
            with open('models/lightgbm_model.pkl', 'rb') as f:
                models['lightgbm'] = pickle.load(f)
        except FileNotFoundError:
            pass
        
        # Load features
        with open('models/features.pkl', 'rb') as f:
            features = pickle.load(f)
        
        loaded_models = list(models.keys())
        print(f"✅ Loaded ensemble models: {', '.join(loaded_models)} ({len(loaded_models)} model{'s' if len(loaded_models) > 1 else ''})")
        return models, features
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("   Please train the model first: python3 enhanced_system_fixed.py --train --years 2023,2024")
        sys.exit(1)

def prepare_features_for_prediction(df_historical, home_team, away_team, week, date):
    """Prepare feature vector for a single game prediction"""
    
    # Get league averages for imputation
    league_avg_score = df_historical['home_score'].mean()
    league_avg_allowed = df_historical['away_score'].mean()
    
    # Calculate features (time-safe)
    def get_team_feature(df, team, value_col, window=5):
        team_games = df[
            ((df['home_team'] == team) | (df['away_team'] == team)) &
            (df['date'] < date)
        ].tail(window)
        
        if len(team_games) == 0:
            return None
        
        values = []
        for _, game in team_games.iterrows():
            if game['home_team'] == team:
                if value_col == 'home_score':
                    values.append(game['home_score'])
                elif value_col == 'away_score':
                    values.append(game['away_score'])
                elif value_col == 'home_win':
                    values.append(game['home_win'])
                elif value_col == 'point_diff':
                    values.append(game['point_diff'])
            else:
                if value_col == 'home_score':
                    values.append(game['away_score'])
                elif value_col == 'away_score':
                    values.append(game['home_score'])
                elif value_col == 'home_win':
                    values.append(1 - game['home_win'])
                elif value_col == 'point_diff':
                    values.append(-game['point_diff'])
        
        return np.mean(values) if values else None
    
    # Build feature dictionary
    feature_dict = {}
    
    # Basic rolling features
    feature_dict['home_avg_points_L5'] = get_team_feature(df_historical, home_team, 'home_score') or league_avg_score
    feature_dict['away_avg_points_L5'] = get_team_feature(df_historical, away_team, 'home_score') or league_avg_score
    feature_dict['home_avg_allowed_L5'] = get_team_feature(df_historical, home_team, 'away_score') or league_avg_allowed
    feature_dict['away_avg_allowed_L5'] = get_team_feature(df_historical, away_team, 'away_score') or league_avg_allowed
    feature_dict['home_win_rate_L5'] = get_team_feature(df_historical, home_team, 'home_win') or 0.5
    feature_dict['away_win_rate_L5'] = get_team_feature(df_historical, away_team, 'home_win') or 0.5
    feature_dict['home_diff_trend'] = get_team_feature(df_historical, home_team, 'point_diff') or 0
    feature_dict['away_diff_trend'] = get_team_feature(df_historical, away_team, 'point_diff') or 0
    
    # Matchup features
    feature_dict['point_spread_estimate'] = feature_dict['home_avg_points_L5'] - feature_dict['away_avg_points_L5'] + 3
    feature_dict['home_advantage'] = 3
    feature_dict['rest_advantage'] = 0
    feature_dict['week'] = week
    
    # Division game
    divisions = {
        'AFC East': ['Buffalo Bills', 'Miami Dolphins', 'New England Patriots', 'New York Jets'],
        'AFC North': ['Baltimore Ravens', 'Cincinnati Bengals', 'Cleveland Browns', 'Pittsburgh Steelers'],
        'AFC South': ['Houston Texans', 'Indianapolis Colts', 'Jacksonville Jaguars', 'Tennessee Titans'],
        'AFC West': ['Denver Broncos', 'Kansas City Chiefs', 'Las Vegas Raiders', 'Los Angeles Chargers'],
        'NFC East': ['Dallas Cowboys', 'New York Giants', 'Philadelphia Eagles', 'Washington Commanders'],
        'NFC North': ['Chicago Bears', 'Detroit Lions', 'Green Bay Packers', 'Minnesota Vikings'],
        'NFC South': ['Atlanta Falcons', 'Carolina Panthers', 'New Orleans Saints', 'Tampa Bay Buccaneers'],
        'NFC West': ['Arizona Cardinals', 'Los Angeles Rams', 'San Francisco 49ers', 'Seattle Seahawks'],
    }
    
    is_division = 0
    for division in divisions.values():
        if home_team in division and away_team in division:
            is_division = 1
            break
    
    feature_dict['is_division_game'] = is_division
    
    # Add all other features with defaults (simplified for prediction)
    feature_dict['home_team_home_advantage'] = 0
    feature_dict['away_team_away_disadvantage'] = 0
    feature_dict['home_momentum'] = 0
    feature_dict['away_momentum'] = 0
    feature_dict['momentum_advantage'] = 0
    feature_dict['home_opponent_strength'] = league_avg_score
    feature_dict['away_opponent_strength'] = league_avg_score
    feature_dict['opponent_strength_diff'] = 0
    feature_dict['week_normalized'] = week / 18.0
    feature_dict['is_early_season'] = 1 if week <= 6 else 0
    feature_dict['is_mid_season'] = 1 if 6 < week <= 12 else 0
    feature_dict['is_late_season'] = 1 if week > 12 else 0
    feature_dict['h2h_home_win_rate'] = 0.5
    feature_dict['h2h_games_played'] = 0
    feature_dict['home_point_diff_variance'] = 0
    feature_dict['away_point_diff_variance'] = 0
    feature_dict['consistency_advantage'] = 0
    feature_dict['home_scoring_trend'] = 0
    feature_dict['away_scoring_trend'] = 0
    feature_dict['scoring_trend_advantage'] = 0
    feature_dict['home_yards_per_play'] = 5.5
    feature_dict['away_yards_per_play'] = 5.5
    feature_dict['home_explosive_rate'] = 0.15
    feature_dict['away_explosive_rate'] = 0.15
    feature_dict['home_third_down_success'] = 0.40
    feature_dict['away_third_down_success'] = 0.40
    feature_dict['home_red_zone_td'] = 0.60
    feature_dict['away_red_zone_td'] = 0.60
    feature_dict['efficiency_advantage'] = 0
    feature_dict['home_team_tier'] = 2
    feature_dict['away_team_tier'] = 2
    feature_dict['tier_matchup'] = 0
    feature_dict['home_form_pca1'] = 0
    feature_dict['home_form_pca2'] = 0
    feature_dict['away_form_pca1'] = 0
    feature_dict['away_form_pca2'] = 0
    feature_dict['coaching_aggression_diff'] = 0
    feature_dict['home_travel_miles_21d'] = 0
    feature_dict['away_travel_miles_21d'] = 0
    feature_dict['home_back_to_back_away'] = 0
    feature_dict['away_back_to_back_away'] = 0
    feature_dict['home_after_long_trip'] = 0
    feature_dict['away_timezone_disadvantage'] = 0
    feature_dict['travel_advantage'] = 0
    feature_dict['home_qb_continuity'] = 1.0
    feature_dict['away_qb_continuity'] = 1.0
    feature_dict['home_ol_continuity'] = 1.0
    feature_dict['away_ol_continuity'] = 1.0
    feature_dict['home_qb_change_flag'] = 0
    feature_dict['away_qb_change_flag'] = 0
    feature_dict['qb_continuity_advantage'] = 0
    feature_dict['home_4th_quarter_perf'] = 0
    feature_dict['away_4th_quarter_perf'] = 0
    feature_dict['fourth_quarter_advantage'] = 0
    feature_dict['home_coach_aggression'] = 0.5
    feature_dict['away_coach_aggression'] = 0.5
    feature_dict['home_adjustment_delta'] = 0
    feature_dict['away_adjustment_delta'] = 0
    feature_dict['market_movement_units'] = 0
    feature_dict['market_closing_line'] = 0
    feature_dict['model_market_divergence'] = 0
    # Calculate prediction confidence (same logic as training)
    def calculate_prediction_confidence(df, home_team, away_team, date):
        """Calculate how predictable this matchup is"""
        home_games = df[
            ((df['home_team'] == home_team) | (df['away_team'] == home_team)) &
            (df['date'] < date)
        ].tail(5)
        
        away_games = df[
            ((df['home_team'] == away_team) | (df['away_team'] == away_team)) &
            (df['date'] < date)
        ].tail(5)
        
        if len(home_games) == 0 or len(away_games) == 0:
            return 0.5
        
        # Calculate consistency
        home_diffs = []
        for _, g in home_games.iterrows():
            if g['home_team'] == home_team:
                home_diffs.append(g['point_diff'])
            else:
                home_diffs.append(-g['point_diff'])
        
        away_diffs = []
        for _, g in away_games.iterrows():
            if g['home_team'] == away_team:
                away_diffs.append(g['point_diff'])
            else:
                away_diffs.append(-g['point_diff'])
        
        home_consistency = 1.0 / (1.0 + np.std(home_diffs)) if len(home_diffs) > 1 else 0.5
        away_consistency = 1.0 / (1.0 + np.std(away_diffs)) if len(away_diffs) > 1 else 0.5
        
        # H2H history
        h2h_games = df[
            (((df['home_team'] == home_team) & (df['away_team'] == away_team)) |
             ((df['home_team'] == away_team) & (df['away_team'] == home_team))) &
            (df['date'] < date)
        ]
        h2h_factor = min(1.0, len(h2h_games) / 5.0)
        
        confidence = (home_consistency + away_consistency) / 2.0 * (0.5 + 0.5 * h2h_factor)
        return confidence
    
    pred_confidence = calculate_prediction_confidence(df_historical, home_team, away_team, date)
    feature_dict['prediction_confidence'] = pred_confidence
    feature_dict['is_high_confidence'] = 1 if pred_confidence > 0.6 else 0
    
    return feature_dict

def predict_todays_games():
    """Predict all games scheduled for today"""
    
    print("="*80)
    print("🎯 PREDICTING TODAY'S NFL GAMES")
    print("="*80)
    
    # Load ensemble models
    models_dict, features = load_ensemble_models()
    
    # Keep backward compatibility: use CatBoost as primary
    model = models_dict.get('catboost')
    
    # Load historical data
    print("\n📥 Loading historical data...")
    try:
        df_historical = pd.read_csv('data/nfl_2023_2024_features.csv')
        df_historical['date'] = pd.to_datetime(df_historical['date'])
        print(f"   ✅ Loaded {len(df_historical)} historical games")
    except FileNotFoundError:
        print("   ⚠️  Features file not found, collecting fresh data...")
        df_2023 = collect_nfl_season_data(2023)
        df_2024 = collect_nfl_season_data(2024)
        df_combined = pd.concat([df_2023, df_2024], ignore_index=True)
        df_historical = engineer_advanced_features(df_combined)
        print(f"   ✅ Collected and processed {len(df_historical)} games")
    
    # Get today's games
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    
    print(f"\n📅 Fetching games for {today.strftime('%B %d, %Y')}...")
    games_today = ESPNAPI.get_scoreboard(dates=today_str)
    
    # Fetch Vegas odds
    print("\n💰 Fetching Vegas odds...")
    odds_cache = VegasOddsAPI.fetch_all_upcoming_odds()
    
    predictions = []
    
    for event in games_today.get('events', []):
        comp = event['competitions'][0]
        
        # Skip completed games
        if event['status']['type']['completed']:
            continue
        
        home = comp['competitors'][0] if comp['competitors'][0]['homeAway'] == 'home' else comp['competitors'][1]
        away = comp['competitors'][1] if comp['competitors'][1]['homeAway'] == 'away' else comp['competitors'][0]
        
        home_team = home['team']['displayName']
        away_team = away['team']['displayName']
        week = event.get('week', {}).get('number', 0)
        game_date = pd.to_datetime(event['date'])
        
        # Prepare features
        feature_dict = prepare_features_for_prediction(
            df_historical, home_team, away_team, week, game_date
        )
        
        # Enhance features with API data (nfl_data_py, weather, injuries, etc.)
        if API_INTEGRATION_AVAILABLE:
            try:
                feature_dict = enhance_features_with_apis(
                    feature_dict=feature_dict,
                    home_team=home_team,
                    away_team=away_team,
                    game_date=game_date,
                    df_historical=df_historical
                )
            except Exception as e:
                # If API enhancement fails, continue with original features
                print(f"   ⚠️  API enhancement failed for {home_team} vs {away_team}: {e}")
        
        # Get Vegas odds
        opening_line, closing_line, movement = VegasOddsAPI.get_odds_for_game(
            home_team, away_team, odds_cache=odds_cache
        )
        
        if closing_line is not None:
            vegas_spread = -closing_line  # Convert to our convention
            feature_dict['market_closing_line'] = vegas_spread
            feature_dict['market_movement_units'] = movement
        else:
            vegas_spread = None
            feature_dict['market_closing_line'] = feature_dict['point_spread_estimate']
            feature_dict['market_movement_units'] = 0
        
        # Create feature vector
        X = pd.DataFrame([feature_dict])[features]
        
        # Ensemble prediction: weighted average of all available models
        predictions_list = []
        weights_list = []
        
        # Default weights (based on typical performance: CatBoost > XGBoost > LightGBM)
        default_weights = {
            'catboost': 0.5,
            'xgboost': 0.3,
            'lightgbm': 0.2
        }
        
        for model_name, model_obj in models_dict.items():
            try:
                pred = float(model_obj.predict(X)[0])
                predictions_list.append(pred)
                weights_list.append(default_weights.get(model_name, 0.33))
            except Exception as e:
                print(f"   ⚠️  {model_name} prediction failed: {e}")
        
        if len(predictions_list) == 0:
            print(f"   ❌ All models failed for {home_team} vs {away_team}")
            continue
        
        # Normalize weights
        weights_array = np.array(weights_list)
        weights_array = weights_array / weights_array.sum()
        
        # Weighted ensemble prediction
        pred_spread = np.average(predictions_list, weights=weights_array)
        
        # Calculate model disagreement (confidence metric)
        if len(predictions_list) > 1:
            disagreement = np.std(predictions_list)
            # Adjust confidence based on model agreement
            if disagreement < 5:
                feature_dict['prediction_confidence'] = min(0.95, feature_dict.get('prediction_confidence', 0.5) + 0.1)
        
        # Calculate divergence from Vegas
        if vegas_spread is not None:
            divergence = abs(pred_spread - vegas_spread)
            feature_dict['model_market_divergence'] = divergence
        else:
            divergence = None
        
        predicted_winner = home_team if pred_spread > 0 else away_team
        
        # Enhanced confidence: combines prediction confidence + prediction strength
        pred_confidence = feature_dict.get('prediction_confidence', 0.5)
        prediction_strength = min(0.95, abs(pred_spread) / 20)  # Larger spread = more confident
        
        # Combined confidence: 60% from matchup predictability, 40% from prediction strength
        # Scale to reflect actual model accuracy (60.5% = base confidence floor)
        base_model_accuracy = 0.605  # From training: 60.5% accuracy
        combined_factor = (pred_confidence * 0.6) + (prediction_strength * 0.4)
        
        # Confidence ranges from base_model_accuracy (0.605) to near 1.0
        # This ensures confidence reflects the model's proven performance
        confidence_score = base_model_accuracy + (combined_factor * (1.0 - base_model_accuracy))
        confidence_score = min(0.95, max(base_model_accuracy, confidence_score))  # Clamp between 0.605 and 0.95
        
        # High confidence: >70% (above model baseline)
        is_high_conf = 1 if confidence_score > 0.7 else 0
        
        # Compute SHAP explanation if available
        shap_explanation = None
        try:
            from shap_explainer import get_shap_explanation_for_prediction
            shap_explanation = get_shap_explanation_for_prediction(
                model=models_dict.get('catboost'),  # Use CatBoost for SHAP
                X=X,
                features=features,
                shap_file='models/shap_values.pkl'
            )
        except Exception as e:
            pass  # Silently fail if SHAP not available
        
        pred_dict = {
            'sport': 'NFL',  # Add sport field
            'date': game_date.strftime('%Y-%m-%d'),
            'week': week,
            'away_team': away_team,
            'home_team': home_team,
            'predicted_spread': round(pred_spread, 2),
            'predicted_winner': predicted_winner,
            'confidence_score': round(confidence_score, 3),
            'is_high_confidence': is_high_conf,
            'vegas_spread': round(vegas_spread, 2) if vegas_spread is not None else None,
            'model_market_divergence': round(divergence, 2) if divergence is not None else None,
            'market_movement': round(movement, 2) if closing_line is not None else None,
            'game_time': game_date.strftime('%I:%M %p') if game_date else 'TBD'
        }
        
        # Add SHAP explanation if available (for AI insights)
        if shap_explanation:
            pred_dict['shap_explanation'] = shap_explanation
        
        predictions.append(pred_dict)
    
    if predictions:
        df_preds = pd.DataFrame(predictions)
        
        # Sort by confidence (high confidence first)
        df_preds = df_preds.sort_values(['is_high_confidence', 'confidence_score'], ascending=[False, False])
        
        # Save to database
        db = PredictionDB()
        saved_count = 0
        for _, pred in df_preds.iterrows():
            try:
                db.save_prediction(pred.to_dict())
                saved_count += 1
            except Exception as e:
                print(f"   ⚠️  Error saving prediction: {e}")
        
        # Also save to CSV for backup
        Path('predictions').mkdir(exist_ok=True)
        df_preds.to_csv(f'predictions/today_{today_str}.csv', index=False)
        
        print(f"\n✅ Generated predictions for {len(predictions)} games")
        print(f"💾 Saved {saved_count} to database")
        print(f"💾 Backup CSV: predictions/today_{today_str}.csv")
        
        return df_preds
    else:
        print("\n⚠️  No upcoming games found for today")
        return pd.DataFrame()

if __name__ == '__main__':
    predictions = predict_todays_games()
    
    if not predictions.empty:
        print("\n" + "="*80)
        print("📊 PREDICTIONS SUMMARY")
        print("="*80)
        
        high_conf = predictions[predictions['is_high_confidence'] == 1]
        if len(high_conf) > 0:
            print(f"\n🎯 HIGH CONFIDENCE GAMES ({len(high_conf)}):")
            for _, row in high_conf.iterrows():
                print(f"   {row['away_team']} @ {row['home_team']}")
                print(f"      Prediction: {row['predicted_winner']} by {abs(row['predicted_spread']):.1f}")
                if row['vegas_spread'] is not None:
                    print(f"      Vegas: {row['vegas_spread']:.1f} | Divergence: {row['model_market_divergence']:.1f}")
        
        print(f"\n📈 Total Games: {len(predictions)}")
        print(f"🎯 High Confidence: {len(high_conf)} ({len(high_conf)/len(predictions)*100:.0f}%)")

