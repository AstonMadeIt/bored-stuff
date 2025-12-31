#!/usr/bin/env python3
"""
NBA Game Prediction System
Uses nba_api package to fetch NBA data and make predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import datetime as dt
import pickle
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

# Import API integration for enhanced features
try:
    from integrate_apis import enhance_features_with_apis
    API_INTEGRATION_AVAILABLE = True
except ImportError:
    API_INTEGRATION_AVAILABLE = False

# Import clutch features analyzer
try:
    from nba_clutch_features import NBAClutchAnalyzer
    CLUTCH_AVAILABLE = True
except ImportError:
    CLUTCH_AVAILABLE = False
    print("⚠️  Clutch features not available")

try:
    from nba_api.stats.endpoints import scoreboardv2, teamgamelog
    from nba_api.live.nba.endpoints import scoreboard as live_scoreboard
    NBA_API_AVAILABLE = True
except ImportError as e:
    NBA_API_AVAILABLE = False
    print(f"⚠️  nba_api not available: {e}")
    print("   Install with: pip install nba_api")

class NBADataCollector:
    """Collect NBA game data using nba_api"""
    
    _team_map = None
    
    @classmethod
    def get_team_map(cls):
        """Get team ID to name mapping"""
        if cls._team_map is None:
            try:
                from nba_api.stats.static import teams
                teams_list = teams.get_teams()
                cls._team_map = {t['id']: t['full_name'] for t in teams_list}
            except:
                cls._team_map = {}
        return cls._team_map
    
    @staticmethod
    def get_scoreboard(season='2024-25', date=None):
        """Get NBA scoreboard for a date"""
        if not NBA_API_AVAILABLE:
            return {'resultSets': []}
        
        try:
            from nba_api.stats.endpoints import scoreboardv2
            
            if date:
                # Format date for NBA API (MM/DD/YYYY)
                date_str = pd.to_datetime(date).strftime('%m/%d/%Y')
                games = scoreboardv2.ScoreboardV2(game_date=date_str)
            else:
                # Get today's games
                today = dt.date.today()
                date_str = today.strftime('%m/%d/%Y')
                games = scoreboardv2.ScoreboardV2(game_date=date_str)
            
            return games.get_dict()
        except Exception as e:
            print(f"   ⚠️  Error fetching NBA scoreboard: {e}")
            return {'resultSets': []}
    
    @staticmethod
    def get_team_games(team_id, season='2024-25'):
        """Get all games for a team"""
        if not NBA_API_AVAILABLE:
            return pd.DataFrame()
        
        try:
            games = teamgamelog.TeamGameLog(team_id=team_id, season=season)
            df = games.get_data_frames()[0]
            return df
        except Exception as e:
            print(f"   ⚠️  Error fetching team games: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def collect_season_data(season='2024-25'):
        """Collect completed games for a season"""
        print(f"\n📥 Collecting {season} NBA season data...")
        
        if not NBA_API_AVAILABLE:
            print("   ❌ nba_api not available")
            return pd.DataFrame()
        
        all_games = []
        
        # Get games for each month of the season
        # NBA season typically runs Oct-April
        season_start = datetime(2024, 10, 1) if '2024' in season else datetime(2023, 10, 1)
        season_end = datetime(2025, 4, 30) if '2024' in season else datetime(2024, 4, 30)
        
        current_date = season_start
        while current_date <= season_end:
            date_str = current_date.strftime('%Y-%m-%d')
            
            try:
                scoreboard_data = NBADataCollector.get_scoreboard(date=date_str)
                
                # Parse scoreboard data
                if 'resultSets' in scoreboard_data:
                    for result_set in scoreboard_data['resultSets']:
                        if result_set.get('name') == 'GameHeader':
                            headers = result_set['headers']
                            rows = result_set['rowSet']
                            
                            # Get team mapping
                            team_map = NBADataCollector.get_team_map()
                            
                            for row in rows:
                                game_dict = dict(zip(headers, row))
                                
                                # Only include completed games
                                if game_dict.get('GAME_STATUS_TEXT') == 'Final':
                                    # Get team names from IDs
                                    home_team_id = game_dict.get('HOME_TEAM_ID')
                                    visitor_team_id = game_dict.get('VISITOR_TEAM_ID')
                                    
                                    home_team_name = team_map.get(home_team_id, f'Team_{home_team_id}')
                                    away_team_name = team_map.get(visitor_team_id, f'Team_{visitor_team_id}')
                                    
                                    all_games.append({
                                        'date': date_str,
                                        'game_id': game_dict.get('GAME_ID'),
                                        'home_team': home_team_name,
                                        'away_team': away_team_name,
                                        'home_score': game_dict.get('HOME_TEAM_PTS', 0),
                                        'away_score': game_dict.get('VISITOR_TEAM_PTS', 0),
                                        'season': season
                                    })
            except Exception as e:
                pass  # Skip dates with errors
            
            current_date += timedelta(days=1)
            
            # Limit to avoid too many API calls
            if len(all_games) > 100:
                break
        
        df = pd.DataFrame(all_games)
        print(f"   ✅ Collected {len(df)} COMPLETED games")
        
        return df

def engineer_nba_features(df):
    """Create ENHANCED NBA features - Critical NBA-specific factors"""
    
    print("\n🔧 Engineering ENHANCED NBA features (Rest, Back-to-Back, Recent Form)...")
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Basic features
    df['point_diff'] = df['home_score'] - df['away_score']
    df['total_points'] = df['home_score'] + df['away_score']
    df['home_win'] = (df['point_diff'] > 0).astype(int)
    df['away_win'] = 1 - df['home_win']
    
    # ===== CRITICAL NBA FEATURE #1: REST & BACK-TO-BACK DETECTION =====
    def get_rest_days(df, team_col, date_col):
        """Calculate days of rest for each team"""
        rest_days = []
        for idx, row in df.iterrows():
            team = row[team_col]
            game_date = row[date_col]
            
            # Find last game for this team before current game
            last_game = df[
                ((df['home_team'] == team) | (df['away_team'] == team)) &
                (df[date_col] < game_date)
            ].tail(1)
            
            if len(last_game) > 0:
                last_date = last_game[date_col].iloc[0]
                days_rest = (game_date - last_date).days
                rest_days.append(days_rest)
            else:
                rest_days.append(2)  # Default: assume normal rest
        
        return rest_days
    
    df['home_rest_days'] = get_rest_days(df, 'home_team', 'date')
    df['away_rest_days'] = get_rest_days(df, 'away_team', 'date')
    
    # Back-to-back flags (CRITICAL - teams on B2B lose ~60% of time)
    df['home_is_b2b'] = (df['home_rest_days'] <= 1).astype(int)
    df['away_is_b2b'] = (df['away_rest_days'] <= 1).astype(int)
    
    # Rest advantage (HUGE EDGE - team with 2+ days rest vs B2B opponent)
    df['rest_advantage'] = df['home_rest_days'] - df['away_rest_days']
    df['rest_advantage_abs'] = df['rest_advantage'].abs()
    
    # Rest categories
    df['home_rest_category'] = df['home_rest_days'].apply(
        lambda x: 0 if x <= 1 else (1 if x == 2 else 2)  # 0=B2B, 1=Normal, 2=Rested
    )
    df['away_rest_category'] = df['away_rest_days'].apply(
        lambda x: 0 if x <= 1 else (1 if x == 2 else 2)
    )
    
    # ===== CRITICAL NBA FEATURE #2: RECENT FORM (Last 10-15 games weighted heavily) =====
    def get_team_rolling_weighted(df, team_col, value_col, window=10, recent_window=5):
        """Get rolling average with recent games weighted 2x"""
        features = []
        for idx, row in df.iterrows():
            team_games = df[
                ((df['home_team'] == row[team_col]) | (df['away_team'] == row[team_col])) &
                (df['date'] < row['date'])
            ].tail(window).sort_values('date')
            
            if len(team_games) >= 3:
                # Weight recent games 2x more
                if len(team_games) >= recent_window:
                    recent = team_games.tail(recent_window)[value_col].mean()
                    older = team_games.head(len(team_games) - recent_window)[value_col].mean()
                    weighted_avg = (recent * 2 + older) / 3
                else:
                    weighted_avg = team_games[value_col].mean()
                features.append(weighted_avg)
            else:
                features.append(np.nan)
        
        return features
    
    def get_team_rolling_simple(df, team_col, value_col, window=10):
        """Simple rolling average"""
        features = []
        for idx, row in df.iterrows():
            team_games = df[
                ((df['home_team'] == row[team_col]) | (df['away_team'] == row[team_col])) &
                (df['date'] < row['date'])
            ].tail(window)
            
            if len(team_games) > 0:
                features.append(team_games[value_col].mean())
            else:
                features.append(np.nan)
        
        return features
    
    # Home team features - LAST 10 GAMES (weighted recent)
    df['home_avg_points_L10'] = get_team_rolling_weighted(df, 'home_team', 'home_score', 10, 5)
    df['home_avg_allowed_L10'] = get_team_rolling_weighted(df, 'home_team', 'away_score', 10, 5)
    df['home_win_rate_L10'] = get_team_rolling_simple(df, 'home_team', 'home_win', 10)
    
    # Away team features - LAST 10 GAMES
    df['away_avg_points_L10'] = get_team_rolling_weighted(df, 'away_team', 'away_score', 10, 5)
    df['away_avg_allowed_L10'] = get_team_rolling_weighted(df, 'away_team', 'home_score', 10, 5)
    df['away_win_rate_L10'] = get_team_rolling_simple(df, 'away_team', 'away_win', 10)
    
    # Also keep last 5 for comparison
    df['home_avg_points_L5'] = get_team_rolling_simple(df, 'home_team', 'home_score', 5)
    df['away_avg_points_L5'] = get_team_rolling_simple(df, 'away_team', 'away_score', 5)
    
    # ===== CRITICAL NBA FEATURE #3: PACE ADJUSTMENT =====
    # Estimate pace from total points (faster pace = more possessions = higher variance)
    df['home_pace_L10'] = get_team_rolling_simple(df, 'home_team', 'total_points', 10)
    df['away_pace_L10'] = get_team_rolling_simple(df, 'away_team', 'total_points', 10)
    df['expected_pace'] = (df['home_pace_L10'] + df['away_pace_L10']) / 2
    df['pace_differential'] = df['home_pace_L10'] - df['away_pace_L10']
    
    # ===== CRITICAL NBA FEATURE #4: OFFENSIVE/DEFENSIVE RATING (Last 10) =====
    # Net rating = offensive rating - defensive rating
    df['home_net_rating_L10'] = df['home_avg_points_L10'] - df['home_avg_allowed_L10']
    df['away_net_rating_L10'] = df['away_avg_points_L10'] - df['away_avg_allowed_L10']
    df['net_rating_advantage'] = df['home_net_rating_L10'] - df['away_net_rating_L10']
    
    # ===== CRITICAL NBA FEATURE #5: HOME/AWAY SPLITS (Recent) =====
    def get_home_away_split(df, team_col, is_home_col, value_col, window=10):
        """Get home/away specific performance"""
        features = []
        for idx, row in df.iterrows():
            team = row[team_col]
            is_home = row[is_home_col]
            
            # Get recent games in same context (home or away)
            team_games = df[
                ((df['home_team'] == team) & (df[is_home_col] == is_home)) |
                ((df['away_team'] == team) & (df[is_home_col] != is_home))
            ].tail(window)
            
            if len(team_games) >= 3:
                # Calculate average points scored in this context
                points = []
                for _, game in team_games.iterrows():
                    if game['home_team'] == team:
                        points.append(game['home_score'])
                    else:
                        points.append(game['away_score'])
                features.append(np.mean(points))
            else:
                features.append(np.nan)
        
        return features
    
    df['home_team_home_avg_L10'] = get_home_away_split(df, 'home_team', pd.Series([True]*len(df)), 'home_score', 10)
    df['away_team_away_avg_L10'] = get_home_away_split(df, 'away_team', pd.Series([False]*len(df)), 'away_score', 10)
    
    # ===== CRITICAL NBA FEATURE #6: STREAK MOMENTUM =====
    def get_streak(df, team_col, date_col, window=10):
        """Get current win/loss streak"""
        streaks = []
        for idx, row in df.iterrows():
            team = row[team_col]
            game_date = row[date_col]
            
            team_games = df[
                ((df['home_team'] == team) | (df['away_team'] == team)) &
                (df[date_col] < game_date)
            ].tail(window).sort_values(date_col, ascending=False)
            
            if len(team_games) > 0:
                wins = []
                for _, game in team_games.iterrows():
                    if game['home_team'] == team:
                        wins.append(game['home_win'])
                    else:
                        wins.append(game['away_win'])
                
                # Count consecutive wins/losses from most recent
                streak_type = wins[0] if wins else 0
                streak_count = 0
                for w in wins:
                    if w == streak_type:
                        streak_count += 1
                    else:
                        break
                
                # Return as signed number (positive = wins, negative = losses)
                streaks.append(streak_count if streak_type == 1 else -streak_count)
            else:
                streaks.append(0)
        
        return streaks
    
    df['home_streak'] = get_streak(df, 'home_team', 'date', 10)
    df['away_streak'] = get_streak(df, 'away_team', 'date', 10)
    df['streak_advantage'] = df['home_streak'] - df['away_streak']
    
    # ===== MATCHUP FEATURES =====
    df['home_advantage'] = 3  # NBA home advantage (~3 points)
    
    # Enhanced spread estimate using all new features
    df['point_spread_estimate'] = (
        df['home_avg_points_L10'] - df['away_avg_points_L10'] + 
        df['home_advantage'] +
        (df['rest_advantage'] * 1.5) +  # Rest advantage worth ~1.5 pts per day
        (df['net_rating_advantage'] * 0.8) +  # Net rating advantage
        (df['streak_advantage'] * 0.5)  # Streak momentum
    )
    
    # Fill NaN values with league averages
    league_avg_score = df['home_score'].mean() if len(df) > 0 else 110
    df['home_avg_points_L10'] = df['home_avg_points_L10'].fillna(league_avg_score)
    df['away_avg_points_L10'] = df['away_avg_points_L10'].fillna(league_avg_score)
    df['home_avg_allowed_L10'] = df['home_avg_allowed_L10'].fillna(league_avg_score)
    df['away_avg_allowed_L10'] = df['away_avg_allowed_L10'].fillna(league_avg_score)
    df['home_win_rate_L10'] = df['home_win_rate_L10'].fillna(0.5)
    df['away_win_rate_L10'] = df['away_win_rate_L10'].fillna(0.5)
    df['home_avg_points_L5'] = df['home_avg_points_L5'].fillna(league_avg_score)
    df['away_avg_points_L5'] = df['away_avg_points_L5'].fillna(league_avg_score)
    df['rest_advantage'] = df['rest_advantage'].fillna(0)
    df['net_rating_advantage'] = df['net_rating_advantage'].fillna(0)
    df['streak_advantage'] = df['streak_advantage'].fillna(0)
    
    print(f"   ✅ Created {len([c for c in df.columns if c not in ['date', 'game_id', 'season']])} features")
    print(f"   🔥 NEW FEATURES: Rest/B2B, Last 10 weighted, Pace, Net Rating, Streaks")
    
    return df

def prepare_nba_features_for_prediction(df_historical, home_team, away_team, date):
    """
    Prepare ENHANCED NBA feature vector for prediction
    Includes: Rest/B2B, Last 10 weighted, Pace, Net Rating, Streaks
    """
    
    # Get league averages
    league_avg_score = df_historical['home_score'].mean() if len(df_historical) > 0 else 110
    
    # Helper function to get team stats
    def get_team_stats(df, team, date, window=10):
        """Get team statistics from last N games"""
        team_games = df[
            ((df['home_team'] == team) | (df['away_team'] == team)) &
            (pd.to_datetime(df['date']) < pd.to_datetime(date))
        ].tail(window).sort_values('date')
        
        if len(team_games) == 0:
            return {
                'points': league_avg_score,
                'allowed': league_avg_score,
                'wins': 0,
                'rest_days': 2,
                'streak': 0,
                'total_points': league_avg_score * 2
            }
        
        points_scored = []
        points_allowed = []
        wins = []
        total_points = []
        
        for _, game in team_games.iterrows():
            if game['home_team'] == team:
                points_scored.append(float(game.get('home_score', 0)))
                points_allowed.append(float(game.get('away_score', 0)))
                wins.append(1 if game.get('home_win', 0) == 1 else 0)
                total_points.append(float(game.get('home_score', 0)) + float(game.get('away_score', 0)))
            else:
                points_scored.append(float(game.get('away_score', 0)))
                points_allowed.append(float(game.get('home_score', 0)))
                wins.append(1 if game.get('home_win', 0) == 0 else 1)
                total_points.append(float(game.get('home_score', 0)) + float(game.get('away_score', 0)))
        
        # Calculate rest days
        last_game_date = pd.to_datetime(team_games.iloc[-1]['date'])
        rest_days = (pd.to_datetime(date) - last_game_date).days
        
        # Cap rest days at reasonable max (if historical data is old, assume normal rest)
        # More than 7 days suggests stale data or off-season
        if rest_days > 7:
            rest_days = 2  # Default to normal rest (2 days between games)
        elif rest_days < 0:
            rest_days = 0  # Can't be negative
        
        # Calculate streak
        streak_type = wins[-1] if wins else 0
        streak_count = 0
        for w in reversed(wins):
            if w == streak_type:
                streak_count += 1
            else:
                break
        streak = streak_count if streak_type == 1 else -streak_count
        
        # Weight recent games 2x
        if len(points_scored) >= 5:
            recent_points = np.mean(points_scored[-5:])
            older_points = np.mean(points_scored[:-5]) if len(points_scored) > 5 else recent_points
            weighted_points = (recent_points * 2 + older_points) / 3
            
            recent_allowed = np.mean(points_allowed[-5:])
            older_allowed = np.mean(points_allowed[:-5]) if len(points_allowed) > 5 else recent_allowed
            weighted_allowed = (recent_allowed * 2 + older_allowed) / 3
        else:
            weighted_points = np.mean(points_scored) if points_scored else league_avg_score
            weighted_allowed = np.mean(points_allowed) if points_allowed else league_avg_score
        
        return {
            'points': weighted_points,
            'allowed': weighted_allowed,
            'wins': np.mean(wins) if wins else 0,
            'rest_days': rest_days,
            'streak': streak,
            'total_points': np.mean(total_points) if total_points else league_avg_score * 2,
            'points_L5': np.mean(points_scored[-5:]) if len(points_scored) >= 5 else np.mean(points_scored) if points_scored else league_avg_score
        }
    
    # Get stats for both teams
    home_stats = get_team_stats(df_historical, home_team, date, 10)
    away_stats = get_team_stats(df_historical, away_team, date, 10)
    
    # Build feature dictionary (matching NFL model features + NBA-specific)
    feature_dict = {}
    
    # Basic rolling features (for compatibility with NFL model)
    feature_dict['home_avg_points_L5'] = home_stats['points_L5']
    feature_dict['away_avg_points_L5'] = away_stats['points_L5']
    feature_dict['home_avg_allowed_L5'] = home_stats['allowed']
    feature_dict['away_avg_allowed_L5'] = away_stats['allowed']
    feature_dict['home_win_rate_L5'] = home_stats['wins']
    feature_dict['away_win_rate_L5'] = away_stats['wins']
    
    # ENHANCED NBA FEATURES
    # Rest & Back-to-Back
    feature_dict['home_rest_days'] = float(home_stats['rest_days'])
    feature_dict['away_rest_days'] = float(away_stats['rest_days'])
    feature_dict['home_is_b2b'] = 1.0 if home_stats['rest_days'] <= 1 else 0.0
    feature_dict['away_is_b2b'] = 1.0 if away_stats['rest_days'] <= 1 else 0.0
    feature_dict['rest_advantage'] = float(home_stats['rest_days'] - away_stats['rest_days'])
    feature_dict['rest_advantage_abs'] = abs(feature_dict['rest_advantage'])
    
    # Last 10 weighted features
    feature_dict['home_avg_points_L10'] = home_stats['points']
    feature_dict['away_avg_points_L10'] = away_stats['points']
    feature_dict['home_avg_allowed_L10'] = home_stats['allowed']
    feature_dict['away_avg_allowed_L10'] = away_stats['allowed']
    
    # Net Rating (Offensive - Defensive)
    feature_dict['home_net_rating_L10'] = home_stats['points'] - home_stats['allowed']
    feature_dict['away_net_rating_L10'] = away_stats['points'] - away_stats['allowed']
    feature_dict['net_rating_advantage'] = feature_dict['home_net_rating_L10'] - feature_dict['away_net_rating_L10']
    
    # Pace
    feature_dict['home_pace_L10'] = home_stats['total_points']
    feature_dict['away_pace_L10'] = away_stats['total_points']
    feature_dict['expected_pace'] = (home_stats['total_points'] + away_stats['total_points']) / 2
    feature_dict['pace_differential'] = home_stats['total_points'] - away_stats['total_points']
    
    # Streaks
    feature_dict['home_streak'] = float(home_stats['streak'])
    feature_dict['away_streak'] = float(away_stats['streak'])
    feature_dict['streak_advantage'] = feature_dict['home_streak'] - feature_dict['away_streak']
    
    # Matchup features
    feature_dict['home_advantage'] = 3.0  # NBA home advantage
    feature_dict['point_spread_estimate'] = (
        feature_dict['home_avg_points_L10'] - feature_dict['away_avg_points_L10'] +
        feature_dict['home_advantage'] +
        (feature_dict['rest_advantage'] * 1.5) +
        (feature_dict['net_rating_advantage'] * 0.8) +
        (feature_dict['streak_advantage'] * 0.5)
    )
    
    # Fill any missing features with defaults (for NFL model compatibility)
    default_features = {
        'home_diff_trend': 0.0,
        'away_diff_trend': 0.0,
        'home_travel_miles_21d': 0.0,
        'away_travel_miles_21d': 0.0,
        'qb_continuity_home': 1.0,
        'qb_continuity_away': 1.0,
        'prediction_confidence': 0.5,
        'is_high_confidence': 0.0
    }
    
    for key, default_val in default_features.items():
        if key not in feature_dict:
            feature_dict[key] = default_val
    
    return feature_dict

def predict_nba_games():
    """Generate predictions for upcoming NBA games"""
    
    if not NBA_API_AVAILABLE:
        print("❌ nba_api not installed. Install with: pip install nba_api")
        return pd.DataFrame()
    
    print("="*80)
    print("🏀 NBA PREDICTIONS - ENHANCED FEATURES + CLUTCH ANALYZER")
    print("="*80)
    print("🔥 Using ENHANCED NBA features: Rest/B2B, Last 10 weighted, Pace, Net Rating, Streaks")
    if CLUTCH_AVAILABLE:
        print("🎯 CLUTCH ANALYZER INTEGRATED: Formula-based late game adjustment active")
        print("   Formula: (Streak × Late Game) / (Record Matchup Divergence - PPG Divergence)")
    else:
        print("⚠️  Clutch Analyzer not available - using standard predictions only")
    print("")
    
    # Load trained CatBoost model (same model used for NFL - works for NBA too)
    model = None
    model_features = None
    
    try:
        models_dict = {}
        # Load CatBoost (primary - always required)
        with open('models/catboost_model.pkl', 'rb') as f:
            models_dict['catboost'] = pickle.load(f)
        
        # Load XGBoost (if available)
        try:
            with open('models/xgboost_model.pkl', 'rb') as f:
                models_dict['xgboost'] = pickle.load(f)
        except FileNotFoundError:
            pass
        
        # Load LightGBM (if available)
        try:
            with open('models/lightgbm_model.pkl', 'rb') as f:
                models_dict['lightgbm'] = pickle.load(f)
        except FileNotFoundError:
            pass
        
        with open('models/features.pkl', 'rb') as f:
            model_features = pickle.load(f)
        
        loaded_models = list(models_dict.keys())
        print(f"✅ Loaded ensemble models: {', '.join(loaded_models)} ({len(loaded_models)} model{'s' if len(loaded_models) > 1 else ''})")
        model = models_dict.get('catboost')  # Keep for backward compatibility
    except FileNotFoundError:
        print("⚠️  Model not found. Train first: python3 enhanced_2.py --train --years 2023,2024")
        print("   Will use simple prediction fallback")
    except Exception as e:
        print(f"⚠️  Error loading model: {e}")
        print("   Will use simple prediction fallback")
    
    # Get upcoming games from ESPN API (better for game times)
    print("\n📥 Fetching upcoming NBA games...")
    try:
        # Try ESPN API first (better time data)
        import requests
        from dateutil import parser
        import pytz
        
        url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
        response = requests.get(url, timeout=10)
        
        upcoming_games = []
        team_name_map = {
            'LA Clippers': 'Los Angeles Clippers',
            'LA Lakers': 'Los Angeles Lakers',
        }
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            for event in events:
                status = event.get('status', {})
                status_type = status.get('type', {})
                
                # Skip completed games
                if status_type.get('completed', False) or status_type.get('name', '').lower() in ['final', 'final/ot']:
                    continue
                
                competitions = event.get('competitions', [])
                if not competitions:
                    continue
                
                comp = competitions[0]
                competitors = comp.get('competitors', [])
                
                if len(competitors) < 2:
                    continue
                
                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                
                if home and away:
                    home_team = team_name_map.get(home['team']['displayName'], home['team']['displayName'])
                    away_team = team_name_map.get(away['team']['displayName'], away['team']['displayName'])
                    
                    # Get game time from event date
                    game_time_est = None
                    date_str = event.get('date', '')
                    if date_str:
                        try:
                            dt = parser.parse(date_str)
                            if dt.tzinfo is None:
                                dt = pytz.UTC.localize(dt)
                            est = pytz.timezone('US/Eastern')
                            dt_est = dt.astimezone(est)
                            game_time_est = dt_est.strftime("%I:%M %p EST")
                        except Exception as e:
                            # Debug: print error
                            pass
                    
                    upcoming_games.append({
                        'date': date_str[:10] if date_str else '',
                        'game_time_est': game_time_est,
                        'home_team': home_team,
                        'away_team': away_team,
                        'game_id': event.get('id', ''),
                        'status': status_type.get('shortDetail', '')
                    })
        
        # Fallback to NBA API if ESPN fails
        if not upcoming_games:
            scoreboard_data = NBADataCollector.get_scoreboard()
            if 'resultSets' in scoreboard_data:
                for result_set in scoreboard_data['resultSets']:
                    if result_set.get('name') == 'GameHeader':
                        headers = result_set['headers']
                        rows = result_set['rowSet']
                        team_map = NBADataCollector.get_team_map()
                        
                        for row in rows:
                            game_dict = dict(zip(headers, row))
                            home_team_id = game_dict.get('HOME_TEAM_ID')
                            visitor_team_id = game_dict.get('VISITOR_TEAM_ID')
                            home_team_name = team_map.get(home_team_id, f'Team_{home_team_id}')
                            away_team_name = team_map.get(visitor_team_id, f'Team_{visitor_team_id}')
                            game_status = game_dict.get('GAME_STATUS_TEXT', '')
                            
                            if game_status not in ['Final', 'Final/OT', 'Final/2OT', 'Final/3OT']:
                                upcoming_games.append({
                                    'date': game_dict.get('GAME_DATE_EST', ''),
                                    'game_time_est': None,
                                    'home_team': home_team_name,
                                    'away_team': away_team_name,
                                    'game_id': game_dict.get('GAME_ID', ''),
                                    'status': game_status
                                })
        
        print(f"   ✅ Found {len(upcoming_games)} upcoming games")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return pd.DataFrame()
    
    if len(upcoming_games) == 0:
        print("   ⚠️  No upcoming games found")
        return pd.DataFrame()
    
    # Load historical data
    print("\n📊 Loading historical NBA data...")
    try:
        df_historical = pd.read_csv('data/nba_2024_features.csv')
        df_historical['date'] = pd.to_datetime(df_historical['date'])
        
        # Check if team names are valid
        if df_historical['home_team'].isna().sum() > len(df_historical) * 0.5:
            print("   ⚠️  Historical data has invalid team names. Recollecting...")
            raise FileNotFoundError("Invalid data")
    except FileNotFoundError:
        print("   ⚠️  Historical data not found or invalid. Collecting...")
        df_raw = NBADataCollector.collect_season_data('2024-25')
        if df_raw.empty:
            print("   ⚠️  No historical data collected")
            return pd.DataFrame()
        df_historical = engineer_nba_features(df_raw)
        df_historical.to_csv('data/nba_2024_features.csv', index=False)
        print(f"   ✅ Collected and saved {len(df_historical)} games")
    
    # Generate predictions (with deduplication)
    predictions = []
    seen_games = set()  # Track (date, home_team, away_team) to prevent duplicates
    
    for game in upcoming_games:
        try:
            home_team = game['home_team']
            away_team = game['away_team']
            game_date = pd.to_datetime(game['date'])
            
            # Deduplicate: Skip if we've already processed this game
            game_key = (str(game_date.date()), home_team, away_team)
            if game_key in seen_games:
                continue  # Skip duplicate
            seen_games.add(game_key)
            
            # Get recent performance (only games before this game's date)
            home_recent = df_historical[
                ((df_historical['home_team'] == home_team) | 
                 (df_historical['away_team'] == home_team)) &
                (df_historical['date'] < game_date)
            ].tail(5)
            
            away_recent = df_historical[
                ((df_historical['home_team'] == away_team) | 
                 (df_historical['away_team'] == away_team)) &
                (df_historical['date'] < game_date)
            ].tail(5)
            
            if len(home_recent) == 0 or len(away_recent) == 0:
                print(f"   ⚠️  Skipping {away_team} @ {home_team} - insufficient history (home: {len(home_recent)}, away: {len(away_recent)})")
                continue
            
            # Build features (simplified - use recent averages)
            # For home team: get their scoring when they were home, or opponent scoring when they were away
            home_scores = []
            for _, g in home_recent.iterrows():
                if g['home_team'] == home_team:
                    home_scores.append(g['home_score'])
                else:
                    home_scores.append(g['away_score'])  # When they were away, get their score
            
            away_scores = []
            for _, g in away_recent.iterrows():
                if g['home_team'] == away_team:
                    away_scores.append(g['home_score'])
                else:
                    away_scores.append(g['away_score'])
            
            home_avg_pts = np.mean(home_scores) if home_scores else 110
            away_avg_pts = np.mean(away_scores) if away_scores else 110
            
            # Use trained CatBoost model with ENHANCED NBA features
            predicted_spread = None
            confidence_score = 0.5
            is_high_conf = 0
            
            if model is not None and model_features is not None:
                try:
                    # Use NBA-specific feature preparation (includes rest/B2B, recent form, pace)
                    feature_dict = prepare_nba_features_for_prediction(
                        df_historical=df_historical,
                        home_team=home_team,
                        away_team=away_team,
                        date=game_date
                    )
                    
                    # Debug: Show rest advantage for first game
                    if len(predictions) == 0:
                        rest_adv = feature_dict.get('rest_advantage', 0)
                        b2b_home = feature_dict.get('home_is_b2b', 0)
                        b2b_away = feature_dict.get('away_is_b2b', 0)
                        print(f"      🔥 ENHANCED FEATURES: Rest advantage={rest_adv:.1f}, Home B2B={b2b_home}, Away B2B={b2b_away}")
                    
                    # Ensure we have all required features (fill missing with defaults)
                    for feat in model_features:
                        if feat not in feature_dict:
                            feature_dict[feat] = 0.0
                    
                    # Create DataFrame with features in correct order
                    X = pd.DataFrame([feature_dict])[model_features]
                    
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
                            pass  # Silently skip failed models
                    
                    if len(predictions_list) == 0:
                        # Fallback to CatBoost only
                        predicted_spread = float(model.predict(X)[0])
                    else:
                        # Normalize weights
                        weights_array = np.array(weights_list)
                        weights_array = weights_array / weights_array.sum()
                        
                        # Weighted ensemble prediction
                        predicted_spread = np.average(predictions_list, weights=weights_array)
                        
                        # Adjust confidence based on model agreement
                        if len(predictions_list) > 1:
                            disagreement = np.std(predictions_list)
                            if disagreement < 5:
                                feature_dict['prediction_confidence'] = min(0.95, feature_dict.get('prediction_confidence', 0.5) + 0.1)
                    
                    # Get prediction confidence from feature dict (calculated during feature prep)
                    pred_confidence = feature_dict.get('prediction_confidence', 0.5)
                    prediction_strength = min(0.95, abs(predicted_spread) / 15)  # Larger spread = more confident
                    
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
                    
                    # ===== APPLY CLUTCH ADJUSTMENT (Your Formula) =====
                    if CLUTCH_AVAILABLE:
                        try:
                            clutch_analyzer = NBAClutchAnalyzer()
                            
                            # Get team records and streaks from standings
                            from standings_fetcher import StandingsFetcher
                            standings = StandingsFetcher()
                            nba_standings = standings.get_nba_standings()
                            
                            # Extract records and streaks
                            home_record = (0, 0)
                            away_record = (0, 0)
                            home_streak = 0
                            away_streak = 0
                            
                            if home_team in nba_standings:
                                home_standings = nba_standings[home_team]
                                home_record = (home_standings.get('wins', 0), home_standings.get('losses', 0))
                                streak_str = home_standings.get('streak', '')
                                if streak_str.startswith('W'):
                                    home_streak = int(streak_str[1:]) if len(streak_str) > 1 else 1
                                elif streak_str.startswith('L'):
                                    home_streak = -int(streak_str[1:]) if len(streak_str) > 1 else -1
                            
                            if away_team in nba_standings:
                                away_standings = nba_standings[away_team]
                                away_record = (away_standings.get('wins', 0), away_standings.get('losses', 0))
                                streak_str = away_standings.get('streak', '')
                                if streak_str.startswith('W'):
                                    away_streak = int(streak_str[1:]) if len(streak_str) > 1 else 1
                                elif streak_str.startswith('L'):
                                    away_streak = -int(streak_str[1:]) if len(streak_str) > 1 else -1
                            
                            # Get PPG from feature dict or calculate
                            home_ppg = feature_dict.get('home_avg_points_L10', home_avg_pts)
                            away_ppg = feature_dict.get('away_avg_points_L10', away_avg_pts)
                            
                            # Calculate clutch adjustment using your formula
                            clutch_result = clutch_analyzer.calculate_clutch_adjustment(
                                home_team=home_team,
                                away_team=away_team,
                                home_streak=home_streak,
                                away_streak=away_streak,
                                home_record=home_record,
                                away_record=away_record,
                                home_ppg=home_ppg,
                                away_ppg=away_ppg,
                                vegas_spread=None
                            )
                            
                            clutch_adjustment = clutch_result['clutch_adjustment']
                            
                            # Apply adjustment to predicted spread
                            predicted_spread_before_clutch = predicted_spread
                            predicted_spread = predicted_spread + clutch_adjustment
                            
                            # Store clutch stats in feature dict for output
                            feature_dict['clutch_adjustment'] = clutch_adjustment
                            feature_dict['clutch_numerator'] = clutch_result['numerator']
                            feature_dict['clutch_denominator'] = clutch_result['denominator']
                            feature_dict['late_game_advantage'] = clutch_result['late_game_advantage']
                            feature_dict['home_clutch_factor'] = clutch_result['home_clutch_factor']
                            feature_dict['away_clutch_factor'] = clutch_result['away_clutch_factor']
                            feature_dict['predicted_spread_before_clutch'] = predicted_spread_before_clutch
                            feature_dict['clutch_analyzer_used'] = True
                            
                            # Always show clutch adjustment in output
                            print(f"      🎯 [CLUTCH ANALYZER] Adjustment: {clutch_adjustment:+.1f} pts")
                            print(f"         Model: {predicted_spread_before_clutch:.1f} → Final: {predicted_spread:.1f}")
                            print(f"         Formula: (Streak×Late Game) / (Record Divergence - PPG Divergence)")
                            print(f"         Home clutch: {clutch_result['home_clutch_factor']:.1f}, Away clutch: {clutch_result['away_clutch_factor']:.1f}")
                            print(f"         Late game advantage: {clutch_result['late_game_advantage']:+.2f}")
                            
                        except Exception as e:
                            # If clutch calculation fails, continue with model prediction
                            print(f"      ⚠️  [CLUTCH ANALYZER] Failed: {e}, using model prediction only")
                            feature_dict['clutch_analyzer_used'] = False
                            feature_dict['clutch_adjustment'] = 0.0
                    else:
                        feature_dict['clutch_analyzer_used'] = False
                        feature_dict['clutch_adjustment'] = 0.0
                    
                except Exception as e:
                    # Fallback to simple prediction if model fails
                    print(f"      ⚠️  Model prediction failed: {e}, using simple prediction")
                    predicted_spread = None
            
            # Fallback to simple prediction if model not available or failed
            if predicted_spread is None:
                predicted_spread = (home_avg_pts - away_avg_pts) + 3
                # Use base confidence for simple predictions (lower than model)
                confidence_score = min(abs(predicted_spread) / 20, 0.95) * 0.5  # Scale down for simple predictions
                is_high_conf = 0
            
            predicted_winner = home_team if predicted_spread > 0 else away_team
            
            # Include enhanced features in prediction output
            pred_dict = {
                'date': game['date'],
                'game_time_est': game.get('game_time_est'),  # Add game time
                'away_team': away_team,
                'home_team': home_team,
                'predicted_spread': round(float(predicted_spread), 1),
                'predicted_winner': predicted_winner,
                'confidence_score': round(float(confidence_score), 3),
                'is_high_confidence': is_high_conf,
                'sport': 'NBA',
                'clutch_analyzer_used': feature_dict.get('clutch_analyzer_used', False) if 'feature_dict' in locals() else False
            }
            
            # Add enhanced NBA features to output (for dashboard display)
            if 'feature_dict' in locals():
                pred_dict['rest_advantage'] = round(float(feature_dict.get('rest_advantage', 0)), 1)
                pred_dict['home_rest_days'] = round(float(feature_dict.get('home_rest_days', 2)), 1)
                pred_dict['away_rest_days'] = round(float(feature_dict.get('away_rest_days', 2)), 1)
                pred_dict['home_is_b2b'] = int(feature_dict.get('home_is_b2b', 0))
                pred_dict['away_is_b2b'] = int(feature_dict.get('away_is_b2b', 0))
                pred_dict['net_rating_advantage'] = round(float(feature_dict.get('net_rating_advantage', 0)), 1)
                pred_dict['streak_advantage'] = round(float(feature_dict.get('streak_advantage', 0)), 1)
                pred_dict['home_avg_points_L10'] = round(float(feature_dict.get('home_avg_points_L10', 0)), 1)
                pred_dict['away_avg_points_L10'] = round(float(feature_dict.get('away_avg_points_L10', 0)), 1)
                
                # Add clutch features if available (BACKEND ONLY - not displayed on dashboard)
                # These are stored for analysis but hidden from public dashboard
                if 'clutch_adjustment' in feature_dict:
                    pred_dict['clutch_adjustment'] = round(float(feature_dict.get('clutch_adjustment', 0)), 2)
                    pred_dict['late_game_advantage'] = round(float(feature_dict.get('late_game_advantage', 0)), 2)
                    pred_dict['home_clutch_factor'] = round(float(feature_dict.get('home_clutch_factor', 0)), 1)
                    pred_dict['away_clutch_factor'] = round(float(feature_dict.get('away_clutch_factor', 0)), 1)
                    # Mark as backend-only (dashboard will skip these fields)
                    pred_dict['_clutch_backend_only'] = True
            
            predictions.append(pred_dict)
            
            print(f"   {away_team} @ {home_team}")
            print(f"      Predicted: {predicted_winner} by {abs(predicted_spread):.1f}")
            
        except Exception as e:
            continue
    
    if predictions:
        df_preds = pd.DataFrame(predictions)
        Path('predictions').mkdir(exist_ok=True)
        df_preds.to_csv('predictions/nba_predictions.csv', index=False)
        print(f"\n✅ Generated {len(predictions)} NBA predictions")
    
    return pd.DataFrame(predictions) if predictions else pd.DataFrame()

if __name__ == '__main__':
    predict_nba_games()

