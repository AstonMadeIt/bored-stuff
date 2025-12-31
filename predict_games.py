#!/usr/bin/env python3
"""
NFL Game Prediction Script
Uses the trained CatBoost model to predict upcoming games
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
import sys

# Import from the main system
sys.path.append(str(Path(__file__).parent))
from enhanced_system_fixed import (
    ESPNAPI, VegasOddsAPI, engineer_advanced_features, collect_nfl_season_data,
    create_rolling_features_safe
)

def load_model_and_features():
    """Load the trained CatBoost model and feature list"""
    try:
        with open('models/catboost_model.pkl', 'rb') as f:
            model = pickle.load(f)
        
        with open('models/features.pkl', 'rb') as f:
            features = pickle.load(f)
        
        print("✅ Loaded CatBoost model and features")
        return model, features
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
    feature_dict['rest_advantage'] = 0  # Would need to calculate from schedule
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
    
    # Home/away splits (simplified - would need full calculation)
    feature_dict['home_team_home_advantage'] = 0
    feature_dict['away_team_away_disadvantage'] = 0
    
    # Momentum (simplified)
    feature_dict['home_momentum'] = 0
    feature_dict['away_momentum'] = 0
    feature_dict['momentum_advantage'] = 0
    
    # Opponent strength
    feature_dict['home_opponent_strength'] = league_avg_score
    feature_dict['away_opponent_strength'] = league_avg_score
    feature_dict['opponent_strength_diff'] = 0
    
    # Time of season
    feature_dict['week_normalized'] = week / 18.0
    feature_dict['is_early_season'] = 1 if week <= 6 else 0
    feature_dict['is_mid_season'] = 1 if 6 < week <= 12 else 0
    feature_dict['is_late_season'] = 1 if week > 12 else 0
    
    # H2H (simplified)
    feature_dict['h2h_home_win_rate'] = 0.5
    feature_dict['h2h_games_played'] = 0
    
    # Variance
    feature_dict['home_point_diff_variance'] = 0
    feature_dict['away_point_diff_variance'] = 0
    feature_dict['consistency_advantage'] = 0
    
    # Scoring trend
    feature_dict['home_scoring_trend'] = 0
    feature_dict['away_scoring_trend'] = 0
    feature_dict['scoring_trend_advantage'] = 0
    
    # Market features (will be filled with real data at prediction time)
    feature_dict['market_movement_units'] = 0
    feature_dict['market_closing_line'] = 0
    feature_dict['model_market_divergence'] = 0
    
    # Additional features needed (simplified for prediction)
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
    
    # Travel-related features (simplified - would need schedule data)
    feature_dict['home_travel_miles_21d'] = 0
    feature_dict['away_travel_miles_21d'] = 0
    feature_dict['home_back_to_back_away'] = 0
    feature_dict['away_back_to_back_away'] = 0
    feature_dict['home_after_long_trip'] = 0
    feature_dict['away_timezone_disadvantage'] = 0
    feature_dict['travel_advantage'] = 0
    
    # QB/OL continuity features (simplified - would need roster data)
    feature_dict['home_qb_continuity'] = 1.0  # Assume continuity
    feature_dict['away_qb_continuity'] = 1.0
    feature_dict['home_ol_continuity'] = 1.0
    feature_dict['away_ol_continuity'] = 1.0
    feature_dict['home_qb_change_flag'] = 0
    feature_dict['away_qb_change_flag'] = 0
    feature_dict['qb_continuity_advantage'] = 0
    
    # 4th quarter performance (simplified - would need play-by-play)
    feature_dict['home_4th_quarter_perf'] = 0
    feature_dict['away_4th_quarter_perf'] = 0
    feature_dict['fourth_quarter_advantage'] = 0
    
    # Coaching features (simplified)
    feature_dict['home_coach_aggression'] = 0.5  # Neutral
    feature_dict['away_coach_aggression'] = 0.5
    feature_dict['home_adjustment_delta'] = 0
    feature_dict['away_adjustment_delta'] = 0
    
    return feature_dict

def predict_upcoming_games(model, features, historical_data):
    """Predict upcoming NFL games"""
    
    print("\n🎯 Fetching upcoming games...")
    
    # Get today's games
    today = datetime.now().strftime('%Y%m%d')
    games_today = ESPNAPI.get_scoreboard(dates=today)
    
    # Fetch ALL Vegas odds in one API call (more efficient!)
    print("\n💰 Fetching Vegas odds (1 API call for all games)...")
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
            historical_data, home_team, away_team, week, game_date
        )
        
        # Get REAL Vegas odds from cache (this is the secret sauce!)
        opening_line, closing_line, movement = VegasOddsAPI.get_odds_for_game(
            home_team, away_team, odds_cache=odds_cache
        )
        
        if closing_line is not None:
            # Vegas line is for home team (negative = home favored, positive = away favored)
            # Our model predicts home team spread (positive = home favored)
            vegas_spread = -closing_line  # Convert to our convention
            feature_dict['market_closing_line'] = vegas_spread
            feature_dict['market_movement_units'] = movement
        else:
            # No odds available (credit limit or API issue)
            vegas_spread = None
            feature_dict['market_closing_line'] = 0
            feature_dict['market_movement_units'] = 0
        
        # Create feature vector
        X = pd.DataFrame([feature_dict])[features]
        
        # Predict
        pred_spread = model.predict(X)[0]
        
        # Calculate model-market divergence (SECRET SAUCE!)
        if vegas_spread is not None:
            divergence = abs(pred_spread - vegas_spread)
            feature_dict['model_market_divergence'] = divergence
            # Re-predict with divergence included
            X = pd.DataFrame([feature_dict])[features]
            pred_spread = model.predict(X)[0]
        else:
            divergence = None
        
        predicted_winner = home_team if pred_spread > 0 else away_team
        confidence = min(0.95, abs(pred_spread) / 20)
        
        predictions.append({
            'away_team': away_team,
            'home_team': home_team,
            'predicted_spread': pred_spread,
            'predicted_winner': predicted_winner,
            'confidence': confidence,
            'week': week,
            'vegas_spread': vegas_spread if vegas_spread is not None else 'N/A',
            'model_market_divergence': divergence if divergence is not None else 'N/A',
            'market_movement': movement if closing_line is not None else 'N/A'
        })
        
        print(f"\n   {away_team} @ {home_team}")
        print(f"      Model Prediction: {predicted_winner} by {abs(pred_spread):.1f} points")
        if vegas_spread is not None:
            vegas_winner = home_team if vegas_spread > 0 else away_team
            print(f"      Vegas Line: {vegas_winner} by {abs(vegas_spread):.1f} points")
            print(f"      Divergence: {divergence:.1f} points", end="")
            if divergence >= 3.0:
                print(" 🎯 HIGH DIVERGENCE - VALUE BET!")
            else:
                print()
            if movement != 0:
                print(f"      Market Movement: {movement:+.1f} points")
        else:
            print(f"      Vegas Line: N/A (credits remaining: {VegasOddsAPI.get_remaining_credits()})")
        print(f"      Confidence: {confidence*100:.0f}%")
    
    if predictions:
        df_preds = pd.DataFrame(predictions)
        df_preds.to_csv('predictions/upcoming_games.csv', index=False)
        print(f"\n   💾 Saved predictions to: predictions/upcoming_games.csv")
        
        # Show high-divergence games (value bets!)
        high_divergence = [p for p in predictions if isinstance(p.get('model_market_divergence'), (int, float)) and p['model_market_divergence'] >= 3.0]
        if high_divergence:
            print("\n" + "="*80)
            print("🎯 HIGH DIVERGENCE GAMES (Potential Value Bets)")
            print("="*80)
            for p in high_divergence:
                print(f"\n   {p['away_team']} @ {p['home_team']}")
                print(f"      Model: {p['predicted_winner']} by {abs(p['predicted_spread']):.1f}")
                print(f"      Vegas: {p['vegas_spread']:.1f}")
                print(f"      Divergence: {p['model_market_divergence']:.1f} points ⚠️")
        
        # Show credit usage
        remaining = VegasOddsAPI.get_remaining_credits()
        used = VegasOddsAPI.CREDIT_LIMIT - remaining
        print(f"\n📊 API Credits: {used}/{VegasOddsAPI.CREDIT_LIMIT} used, {remaining} remaining")
    
    return predictions

def main():
    print("="*80)
    print("NFL GAME PREDICTIONS - CatBoost Model")
    print("="*80)
    
    # Load model
    model, features = load_model_and_features()
    
    # Load historical data for feature calculation
    print("\n📥 Loading historical data...")
    try:
        # Try to load from saved features file
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
    
    # Make predictions
    predictions = predict_upcoming_games(model, features, df_historical)
    
    if predictions:
        print("\n" + "="*80)
        print("✅ PREDICTIONS COMPLETE")
        print("="*80)
        print(f"\nPredicted {len(predictions)} upcoming games")
        print("Check predictions/upcoming_games.csv for full details")
    else:
        print("\n   ⚠️  No upcoming games found for today")

if __name__ == '__main__':
    main()

