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
        self.api_key = api_key or os.getenv('THEODDSAPI_KEY')
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
                                            # DraftKings spread: positive = home favored, negative = away favored
                                            home_spread = home_outcome.get('point', 0)
                                            away_spread = away_outcome.get('point', 0)
                                            
                                            # Use home spread (standard convention)
                                            dk_odds = {
                                                'spread': home_spread,
                                                'home_spread': home_spread,
                                                'away_spread': away_spread,
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
        # Normalize team names to match TheOddsAPI format
        team_name_map = {
            'Los Angeles Clippers': 'LA Clippers',
            'Los Angeles Lakers': 'LA Lakers',
            'Philadelphia 76ers': 'Philadelphia 76ers',
            'Portland Trail Blazers': 'Portland Trail Blazers',
        }
        
        home_normalized = team_name_map.get(home_team, home_team)
        away_normalized = team_name_map.get(away_team, away_team)
        
        odds_dict = self.fetch_nba_odds()
        
        # Try exact match first
        if (home_normalized, away_normalized) in odds_dict:
            return odds_dict[(home_normalized, away_normalized)]
        
        # Try reverse (away, home)
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
        
        return None

