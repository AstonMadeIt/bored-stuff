#!/usr/bin/env python3
"""
API Integration Module
Integrates multiple free APIs to enhance model accuracy
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from pathlib import Path

# ============================================================================
# NFLFASTR INTEGRATION (Highest Impact)
# ============================================================================

class NFLDataPyIntegration:
    """Integrate nfl_data_py for real play-by-play data (Python equivalent of nflfastR)"""
    
    @staticmethod
    def is_available():
        """Check if nfl_data_py is installed"""
        try:
            import nfl_data_py as nfl
            return True
        except ImportError:
            return False
    
    @staticmethod
    def get_team_efficiency_metrics(team, date, years=[2023, 2024]):
        """
        Get REAL efficiency metrics from play-by-play data
        Replaces approximated metrics
        
        Note: Team names need to match nfl_data_py format (e.g., 'BUF', 'MIA', etc.)
        """
        if not NFLDataPyIntegration.is_available():
            return None
        
        try:
            import nfl_data_py as nfl
            
            # Load play-by-play data
            pbp = nfl.import_pbp_data(years)
            
            # Convert team name to abbreviation if needed
            team_abbr = NFLDataPyIntegration._team_name_to_abbr(team)
            if not team_abbr:
                return None
            
            # Filter to team's games before this date
            # Fix datetime comparison: ensure both are timezone-naive
            if 'game_date' in pbp.columns:
                pbp['game_date'] = pd.to_datetime(pbp['game_date'])
                if pbp['game_date'].dt.tz is not None:
                    pbp['game_date'] = pbp['game_date'].dt.tz_localize(None)
            
            date_compare = pd.to_datetime(date)
            if hasattr(date_compare, 'tz') and date_compare.tz is not None:
                date_compare = date_compare.tz_localize(None)
            elif isinstance(date_compare, pd.Timestamp) and date_compare.tz is not None:
                date_compare = date_compare.tz_localize(None)
            
            team_pbp = pbp[
                (pbp['posteam'] == team_abbr) & 
                (pbp['game_date'] < date_compare)
            ].tail(5)  # Last 5 games
            
            if len(team_pbp) == 0:
                return None
            
            # Calculate real metrics
            metrics = {
                'epa_per_play': team_pbp['epa'].mean() if 'epa' in team_pbp.columns else None,
                'success_rate': team_pbp['success'].mean() if 'success' in team_pbp.columns else None,
                'explosive_play_rate': (team_pbp['yards_gained'] > 15).mean() if 'yards_gained' in team_pbp.columns else None,
                'third_down_success': team_pbp[team_pbp['down'] == 3]['success'].mean() if 'down' in team_pbp.columns else None,
                'red_zone_td_rate': team_pbp[team_pbp['yardline_100'] <= 20]['touchdown'].mean() if 'yardline_100' in team_pbp.columns else None,
            }
            
            return metrics
            
        except Exception as e:
            print(f"   ⚠️  nfl_data_py error: {e}")
            return None
    
    @staticmethod
    def _team_name_to_abbr(team_name):
        """Convert full team name to NFL abbreviation"""
        team_map = {
            'Buffalo Bills': 'BUF', 'Miami Dolphins': 'MIA', 'New England Patriots': 'NE',
            'New York Jets': 'NYJ', 'Baltimore Ravens': 'BAL', 'Cincinnati Bengals': 'CIN',
            'Cleveland Browns': 'CLE', 'Pittsburgh Steelers': 'PIT', 'Houston Texans': 'HOU',
            'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX', 'Tennessee Titans': 'TEN',
            'Denver Broncos': 'DEN', 'Kansas City Chiefs': 'KC', 'Las Vegas Raiders': 'LV',
            'Los Angeles Chargers': 'LAC', 'Dallas Cowboys': 'DAL', 'New York Giants': 'NYG',
            'Philadelphia Eagles': 'PHI', 'Washington Commanders': 'WAS', 'Chicago Bears': 'CHI',
            'Detroit Lions': 'DET', 'Green Bay Packers': 'GB', 'Minnesota Vikings': 'MIN',
            'Atlanta Falcons': 'ATL', 'Carolina Panthers': 'CAR', 'New Orleans Saints': 'NO',
            'Tampa Bay Buccaneers': 'TB', 'Arizona Cardinals': 'ARI', 'Los Angeles Rams': 'LAR',
            'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA'
        }
        return team_map.get(team_name)

# ============================================================================
# WEATHER API INTEGRATION
# ============================================================================

class WeatherAPI:
    """Get weather data for games"""
    
    # Stadium locations (approximate coordinates)
    STADIUM_LOCATIONS = {
        'Buffalo Bills': {'lat': 42.7738, 'lon': -78.7869},
        'Miami Dolphins': {'lat': 25.9581, 'lon': -80.2389},
        'New England Patriots': {'lat': 42.0909, 'lon': -71.2643},
        'New York Jets': {'lat': 40.8136, 'lon': -74.0744},
        'New York Giants': {'lat': 40.8136, 'lon': -74.0744},
        # Add more as needed
    }
    
    # Indoor stadiums (no weather impact)
    INDOOR_STADIUMS = [
        'Dallas Cowboys', 'Detroit Lions', 'Houston Texans', 
        'Indianapolis Colts', 'Minnesota Vikings', 'New Orleans Saints',
        'Atlanta Falcons', 'Arizona Cardinals', 'Los Angeles Rams',
        'Los Angeles Chargers'
    ]
    
    @staticmethod
    def get_weather(stadium_name, game_date, api_key=None):
        """
        Get weather for a game
        Uses OpenWeatherMap API (free tier: 1000 calls/day)
        """
        # Check if indoor
        if any(indoor in stadium_name for indoor in WeatherAPI.INDOOR_STADIUMS):
            return {
                'temperature': 72,  # Controlled
                'wind_speed': 0,
                'precipitation': 0,
                'is_dome': True
            }
        
        # Get stadium location
        location = WeatherAPI.STADIUM_LOCATIONS.get(stadium_name)
        if not location:
            # Default to neutral weather
            return {
                'temperature': 65,
                'wind_speed': 5,
                'precipitation': 0,
                'is_dome': False
            }
        
        # If API key provided, fetch real weather
        if api_key:
            try:
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    'lat': location['lat'],
                    'lon': location['lon'],
                    'appid': api_key,
                    'units': 'imperial',
                    'dt': int(game_date.timestamp())
                }
                
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'temperature': data['main']['temp'],
                        'wind_speed': data['wind']['speed'],
                        'precipitation': data.get('rain', {}).get('1h', 0) or data.get('snow', {}).get('1h', 0),
                        'is_dome': False
                    }
            except Exception as e:
                pass
        
        # Default (no API key or error)
        return {
            'temperature': 65,
            'wind_speed': 5,
            'precipitation': 0,
            'is_dome': False
        }

# ============================================================================
# INJURY DATA INTEGRATION
# ============================================================================

class InjuryDataAPI:
    """Get injury data for games"""
    
    @staticmethod
    def get_injury_status(team, game_date, source='espn'):
        """
        Get injury status for key players
        Sources: ESPN API, ClearSports API, or scraping
        """
        # Placeholder - would integrate with actual API
        # For now, return default (all healthy)
        return {
            'qb_status': 'healthy',  # healthy/questionable/out
            'key_players_out': 0,
            'injury_severity_score': 0,  # 0-5 scale
            'backup_qb_quality': 0.5  # 0-1 scale
        }
    
    @staticmethod
    def get_injury_impact_score(injury_data):
        """Calculate impact of injuries on game"""
        score = 0
        
        # QB out = massive impact
        if injury_data['qb_status'] == 'out':
            score += 3.0
        elif injury_data['qb_status'] == 'questionable':
            score += 1.5
        
        # Key players out
        score += injury_data['key_players_out'] * 0.5
        
        # Injury severity
        score += injury_data['injury_severity_score'] * 0.3
        
        return min(score, 5.0)  # Cap at 5

# ============================================================================
# ENHANCED BETTING LINE FEATURES
# ============================================================================

class EnhancedBettingFeatures:
    """Enhanced betting line analysis"""
    
    @staticmethod
    def calculate_line_velocity(opening_line, closing_line, hours_between):
        """
        Calculate how fast the line moved
        Fast movement = sharp money
        """
        if hours_between == 0:
            return 0
        
        movement = closing_line - opening_line
        velocity = abs(movement) / hours_between
        
        return velocity
    
    @staticmethod
    def detect_reverse_movement(opening_line, closing_line, public_percentage=None):
        """
        Detect if line moved against public betting
        This is a STRONG signal (sharp money)
        """
        movement = closing_line - opening_line
        
        # If public bets heavily on one side but line moves other way = sharp money
        if public_percentage:
            if public_percentage > 70 and movement < 0:
                return True  # Public on favorite, line moved down = sharp on underdog
            elif public_percentage < 30 and movement > 0:
                return True  # Public on underdog, line moved up = sharp on favorite
        
        return False
    
    @staticmethod
    def calculate_sharp_money_indicator(opening_line, closing_line, movement_velocity, public_pct=None):
        """
        Combined indicator of sharp money activity
        Higher = more sharp money detected
        """
        score = 0
        
        # Fast movement = sharp activity
        if movement_velocity > 0.5:  # 0.5 points per hour
            score += 2
        
        # Reverse movement = very sharp
        if EnhancedBettingFeatures.detect_reverse_movement(opening_line, closing_line, public_pct):
            score += 3
        
        # Large movement = significant sharp money
        if abs(closing_line - opening_line) > 2:
            score += 1
        
        return min(score, 5.0)

# ============================================================================
# PLAYER PERFORMANCE TRENDS
# ============================================================================

class PlayerPerformanceAPI:
    """Get player-level performance trends"""
    
    @staticmethod
    def get_qb_recent_form(team, date, df_historical):
        """
        Get QB's recent performance (last 3 games)
        More accurate than team averages
        """
        # Simplified - would use nflfastR or ESPN API for real QB stats
        # For now, approximate from team scoring consistency
        
        team_games = df_historical[
            ((df_historical['home_team'] == team) | (df_historical['away_team'] == team)) &
            (df_historical['date'] < date)
        ].tail(3)
        
        if len(team_games) == 0:
            return {'rating': 85, 'tds': 2, 'ints': 1}
        
        # Approximate QB stats from team scoring
        avg_points = []
        for _, g in team_games.iterrows():
            if g['home_team'] == team:
                avg_points.append(g['home_score'])
            else:
                avg_points.append(g['away_score'])
        
        avg_pts = np.mean(avg_points)
        
        # Rough QB rating approximation
        qb_rating = 70 + (avg_pts - 20) * 2  # Scale with scoring
        
        return {
            'rating': max(60, min(120, qb_rating)),
            'tds': max(1, int(avg_pts / 7)),
            'ints': max(0, int((25 - avg_pts) / 10))
        }
    
    @staticmethod
    def get_player_momentum_score(team, date, df_historical):
        """
        Calculate player momentum (recent form vs older form)
        """
        team_games = df_historical[
            ((df_historical['home_team'] == team) | (df_historical['away_team'] == team)) &
            (df_historical['date'] < date)
        ].tail(5)
        
        if len(team_games) < 3:
            return 0
        
        # Get recent vs older scoring
        scores = []
        for _, g in team_games.iterrows():
            if g['home_team'] == team:
                scores.append(g['home_score'])
            else:
                scores.append(g['away_score'])
        
        recent_avg = np.mean(scores[-2:]) if len(scores) >= 2 else 0
        older_avg = np.mean(scores[:-2]) if len(scores) > 2 else recent_avg
        
        momentum = recent_avg - older_avg
        return momentum

# ============================================================================
# MAIN INTEGRATION FUNCTION
# ============================================================================

def enhance_features_with_apis(feature_dict, home_team, away_team, game_date, df_historical=None):
    """
    Enhance feature dictionary with data from multiple APIs
    """
    enhanced = feature_dict.copy()
    
    # 1. nfl_data_py efficiency metrics (if available)
    if NFLDataPyIntegration.is_available():
        home_eff = NFLDataPyIntegration.get_team_efficiency_metrics(home_team, game_date)
        away_eff = NFLDataPyIntegration.get_team_efficiency_metrics(away_team, game_date)
        
        if home_eff and away_eff:
            # Replace approximated metrics with real ones
            enhanced['home_yards_per_play'] = home_eff.get('epa_per_play', enhanced.get('home_yards_per_play', 5.5))
            enhanced['away_yards_per_play'] = away_eff.get('epa_per_play', enhanced.get('away_yards_per_play', 5.5))
            enhanced['home_explosive_rate'] = home_eff.get('explosive_play_rate', enhanced.get('home_explosive_rate', 0.15))
            enhanced['away_explosive_rate'] = away_eff.get('explosive_play_rate', enhanced.get('away_explosive_rate', 0.15))
            enhanced['home_third_down_success'] = home_eff.get('third_down_success', enhanced.get('home_third_down_success', 0.40))
            enhanced['away_third_down_success'] = away_eff.get('third_down_success', enhanced.get('away_third_down_success', 0.40))
            enhanced['home_red_zone_td'] = home_eff.get('red_zone_td_rate', enhanced.get('home_red_zone_td', 0.60))
            enhanced['away_red_zone_td'] = away_eff.get('red_zone_td_rate', enhanced.get('away_red_zone_td', 0.60))
    
    # 2. Weather data
    weather = WeatherAPI.get_weather(home_team, game_date)
    enhanced['game_temperature'] = weather['temperature']
    enhanced['wind_speed'] = weather['wind_speed']
    enhanced['precipitation'] = weather['precipitation']
    enhanced['is_dome_game'] = weather['is_dome']
    
    # Weather impact features
    if not weather['is_dome']:
        # Cold weather = lower scoring
        enhanced['weather_scoring_impact'] = max(-5, min(0, (weather['temperature'] - 50) / 10))
        # Wind affects passing
        enhanced['wind_passing_impact'] = -weather['wind_speed'] * 0.1
        # Rain = run-heavy
        enhanced['precipitation_impact'] = -weather['precipitation'] * 0.5
    else:
        enhanced['weather_scoring_impact'] = 0
        enhanced['wind_passing_impact'] = 0
        enhanced['precipitation_impact'] = 0
    
    # 3. Injury data
    home_injuries = InjuryDataAPI.get_injury_status(home_team, game_date)
    away_injuries = InjuryDataAPI.get_injury_status(away_team, game_date)
    
    enhanced['home_injury_impact'] = InjuryDataAPI.get_injury_impact_score(home_injuries)
    enhanced['away_injury_impact'] = InjuryDataAPI.get_injury_impact_score(away_injuries)
    enhanced['injury_advantage'] = away_injuries['injury_severity_score'] - home_injuries['injury_severity_score']
    
    # 4. Player performance trends
    if df_historical is not None:
        home_qb_form = PlayerPerformanceAPI.get_qb_recent_form(home_team, game_date, df_historical)
        away_qb_form = PlayerPerformanceAPI.get_qb_recent_form(away_team, game_date, df_historical)
        
        enhanced['home_qb_recent_rating'] = home_qb_form['rating']
        enhanced['away_qb_recent_rating'] = away_qb_form['rating']
        enhanced['qb_rating_advantage'] = home_qb_form['rating'] - away_qb_form['rating']
        
        home_momentum = PlayerPerformanceAPI.get_player_momentum_score(home_team, game_date, df_historical)
        away_momentum = PlayerPerformanceAPI.get_player_momentum_score(away_team, game_date, df_historical)
        enhanced['player_momentum_advantage'] = home_momentum - away_momentum
    
    return enhanced

if __name__ == '__main__':
    print("API Integration Module")
    print("="*80)
    print(f"nfl_data_py available: {NFLDataPyIntegration.is_available()}")
    print("Install with: pip install nfl-data-py")
    print("\nWeather API: OpenWeatherMap (free tier available)")
    print("Injury API: ESPN/ClearSports (free tiers available)")

