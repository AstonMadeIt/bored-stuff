#!/usr/bin/env python3
"""
Odds Fetcher - Fetch DraftKings odds from TheOddsAPI
Free tier: 500 requests/month
"""

import requests
import os
from datetime import datetime
from typing import Optional, Dict

class OddsFetcher:
    """Fetch betting odds from TheOddsAPI (includes DraftKings)"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Try multiple sources for API key
        if api_key:
            self.api_key = api_key
        elif os.getenv('THEODDSAPI_KEY'):
            self.api_key = os.getenv('THEODDSAPI_KEY')
        elif os.path.exists(os.path.expanduser('~/.theoddsapi_key')):
            with open(os.path.expanduser('~/.theoddsapi_key'), 'r') as f:
                self.api_key = f.read().strip()
        else:
            self.api_key = None
        self.base_url = 'https://api.the-odds-api.com/v4'
        
    def fetch_nba_odds(self, sport='basketball_nba', regions='us', markets='spreads', odds_format='american'):
        """
        Fetch NBA odds from TheOddsAPI
        
        Returns:
            Dict mapping (home_team, away_team) -> odds data
        """
        if not self.api_key:
            return {}
        
        try:
            url = f"{self.base_url}/sports/{sport}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': regions,
                'markets': markets,
                'oddsFormat': odds_format
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                odds_dict = {}
                
                for game in data:
                    home_team = game.get('home_team', '')
                    away_team = game.get('away_team', '')
                    
                    # Find DraftKings bookmaker
                    bookmakers = game.get('bookmakers', [])
                    dk_odds = None
                    
                    for bookmaker in bookmakers:
                        if bookmaker.get('key') == 'draftkings':
                            markets_data = bookmaker.get('markets', [])
                            for market in markets_data:
                                if market.get('key') == 'spreads':
                                    outcomes = market.get('outcomes', [])
                                    if len(outcomes) >= 2:
                                        # Find home and away spreads
                                        home_outcome = next((o for o in outcomes if o.get('name') == home_team), None)
                                        away_outcome = next((o for o in outcomes if o.get('name') == away_team), None)
                                        
                                        if home_outcome and away_outcome:
                                            # TheOddsAPI returns point values:
                                            # +5.5 for home = home getting points (underdog)
                                            # -5.5 for away = away giving points (favorite)
                                            # So if home = +5.5, away is favored by 5.5
                                            
                                            home_point = home_outcome.get('point', 0)
                                            away_point = away_outcome.get('point', 0)
                                            
                                            # Convert to model convention:
                                            # Model uses: Negative = away favored, Positive = home favored
                                            # TheOddsAPI: home_point positive = home getting points (underdog)
                                            #             home_point negative = home giving points (favorite)
                                            
                                            # If home_point is positive: home is underdog, away is favorite
                                            # If home_point is negative: home is favorite, away is underdog
                                            
                                            if home_point > 0:
                                                # Home getting points = away favored
                                                # Store as negative (away favored by abs(home_point))
                                                model_spread = -abs(home_point)
                                            elif home_point < 0:
                                                # Home giving points = home favored
                                                # Store as positive (home favored by abs(home_point))
                                                model_spread = abs(home_point)
                                            else:
                                                # Pick'em
                                                model_spread = 0.0
                                            
                                            dk_odds = {
                                                'spread': model_spread,  # In model convention
                                                'home_spread': home_point,  # Raw from API
                                                'away_spread': away_point,  # Raw from API
                                                'bookmaker': 'DraftKings',
                                                'last_update': bookmaker.get('last_update', '')
                                            }
                                            break
                            
                            if dk_odds:
                                break
                    
                    if dk_odds:
                        odds_dict[(home_team, away_team)] = dk_odds
                
                return odds_dict
            else:
                print(f"   ⚠️  TheOddsAPI error: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"   ⚠️  Error fetching odds: {e}")
            return {}
    
    def get_game_odds(self, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Get odds for a specific game
        
        Args:
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            Dict with spread, or None if not found
        """
        # Comprehensive team name mapping (ESPN -> TheOddsAPI)
        team_name_map = {
            'Los Angeles Clippers': 'LA Clippers',
            'LA Clippers': 'LA Clippers',
            'Los Angeles Lakers': 'LA Lakers',
            'LA Lakers': 'LA Lakers',
            'Philadelphia 76ers': 'Philadelphia 76ers',
            'Portland Trail Blazers': 'Portland Trail Blazers',
            'Golden State Warriors': 'Golden State Warriors',
            'Charlotte Hornets': 'Charlotte Hornets',
            'Minnesota Timberwolves': 'Minnesota Timberwolves',
            'Atlanta Hawks': 'Atlanta Hawks',
            'Orlando Magic': 'Orlando Magic',
            'Indiana Pacers': 'Indiana Pacers',
            'Phoenix Suns': 'Phoenix Suns',
            'Cleveland Cavaliers': 'Cleveland Cavaliers',
            'New Orleans Pelicans': 'New Orleans Pelicans',
            'Chicago Bulls': 'Chicago Bulls',
            'New York Knicks': 'New York Knicks',
            'San Antonio Spurs': 'San Antonio Spurs',
            'Denver Nuggets': 'Denver Nuggets',
            'Toronto Raptors': 'Toronto Raptors',
            'Washington Wizards': 'Washington Wizards',
            'Milwaukee Bucks': 'Milwaukee Bucks',
            'Portland Trail Blazers': 'Portland Trail Blazers',
            'Oklahoma City Thunder': 'Oklahoma City Thunder',
        }
        
        home_normalized = team_name_map.get(home_team, home_team)
        away_normalized = team_name_map.get(away_team, away_team)
        
        odds_dict = self.fetch_nba_odds()
        
        # Try exact match first
        if (home_normalized, away_normalized) in odds_dict:
            return odds_dict[(home_normalized, away_normalized)]
        
        # Try reverse (away, home) - TheOddsAPI might have them swapped
        if (away_normalized, home_normalized) in odds_dict:
            odds = odds_dict[(away_normalized, home_normalized)]
            # Flip the spread if teams are reversed
            return {
                'spread': -odds['spread'],
                'home_spread': -odds['home_spread'],
                'away_spread': -odds['away_spread'],
                'bookmaker': odds['bookmaker'],
                'last_update': odds['last_update']
            }
        
        # Try fuzzy matching (partial name match)
        for (api_home, api_away), odds_data in odds_dict.items():
            # Check if team names match (case-insensitive, partial)
            if (home_normalized.lower() in api_home.lower() or api_home.lower() in home_normalized.lower()) and \
               (away_normalized.lower() in api_away.lower() or api_away.lower() in away_normalized.lower()):
                return odds_data
            
            # Try reversed
            if (home_normalized.lower() in api_away.lower() or api_away.lower() in home_normalized.lower()) and \
               (away_normalized.lower() in api_home.lower() or api_home.lower() in away_normalized.lower()):
                return {
                    'spread': -odds_data['spread'],
                    'home_spread': -odds_data['home_spread'],
                    'away_spread': -odds_data['away_spread'],
                    'bookmaker': odds_data['bookmaker'],
                    'last_update': odds_data['last_update']
                }
        
        return None

