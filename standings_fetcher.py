#!/usr/bin/env python3
"""
Standings Fetcher - Real NBA/NFL Standings from Official APIs
Fetches current season records, streaks, and L10 from official sources
"""

import pandas as pd
from typing import Dict, Optional
import requests
from datetime import datetime, timedelta

class StandingsFetcher:
    """Fetch real standings from NBA and NFL APIs"""
    
    def __init__(self):
        self.nba_cache = {}
        self.nfl_cache = {}
        self.cache_time = None
        self._fetching_nba = False  # Prevent concurrent fetches
        self._fetching_nfl = False
    
    def get_nba_standings(self) -> Dict[str, Dict]:
        """
        Get NBA standings by scraping ESPN's standings page
        Returns: {team_name: {'wins': int, 'losses': int, 'streak': str, 'l10': str, 'record': str}}
        """
        # Return cached if available and recent (< 5 minutes old)
        if self.nba_cache and self.cache_time:
            time_diff = (datetime.now() - self.cache_time).total_seconds()
            if time_diff < 300:  # 5 minutes
                return self.nba_cache
        
        # Prevent concurrent fetches
        if self._fetching_nba:
            return self.nba_cache if self.nba_cache else {}
        
        self._fetching_nba = True
        try:
            from bs4 import BeautifulSoup
            import re
            
            # Scrape ESPN standings page
            url = "https://www.espn.com/nba/standings"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return self.nba_cache if self.nba_cache else {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            standings_dict = {}
            
            # ESPN uses 2 tables per conference: team names (table 1) and stats (table 2)
            tables = soup.find_all('table')
            
            # Process pairs of tables (each conference has 2 tables)
            for table_idx in range(0, len(tables), 2):
                if table_idx + 1 >= len(tables):
                    break
                
                team_table = tables[table_idx]
                stats_table = tables[table_idx + 1]
                
                # Get rows (skip header row)
                team_rows = team_table.find_all('tr')[1:]
                stats_rows = stats_table.find_all('tr')[1:]
                
                # Match teams with stats by row index
                for i in range(min(len(team_rows), len(stats_rows))):
                    # Extract team name from first table
                    team_cell = team_rows[i].find('td')
                    if not team_cell:
                        continue
                    
                    team_text = team_cell.get_text().strip()
                    # Format: "1DETDetroit Pistons" -> extract "Detroit Pistons"
                    match = re.search(r'\d+[A-Z]{2,3}(.+?)$', team_text)
                    if match:
                        team_name = match.group(1).strip()
                    else:
                        team_name = team_text
                    
                    if not team_name or len(team_name) < 3:
                        continue
                    
                    # Normalize team name
                    team_name = self._normalize_nba_team_name(team_name)
                    
                    # Extract stats from second table
                    stats_cells = stats_rows[i].find_all('td')
                    if len(stats_cells) < 2:
                        continue
                    
                    # W and L are first two cells
                    try:
                        wins = int(stats_cells[0].get_text().strip())
                        losses = int(stats_cells[1].get_text().strip())
                    except (ValueError, IndexError):
                        continue
                    
                    # Extract PPG and OPP PPG
                    # Column order: W(0), L(1), PCT(2), GB(3), HOME(4), AWAY(5), DIV(6), CONF(7), PPG(8), OPP PPG(9), DIFF(10), STRK(11), L10(12)
                    ppg = 0.0
                    opp_ppg = 0.0
                    
                    # PPG is column 8, OPP PPG is column 9
                    if len(stats_cells) >= 10:
                        try:
                            ppg_text = stats_cells[8].get_text().strip()
                            opp_ppg_text = stats_cells[9].get_text().strip()
                            ppg = float(ppg_text) if ppg_text else 0.0
                            opp_ppg = float(opp_ppg_text) if opp_ppg_text else 0.0
                        except (ValueError, IndexError):
                            pass
                    
                    # STRK is second-to-last column, L10 is last
                    l10 = 'N/A'
                    streak = 'N/A'
                    
                    if len(stats_cells) >= 2:
                        # STRK is second-to-last column
                        streak_text = stats_cells[-2].get_text().strip()
                        if streak_text:
                            streak = streak_text
                        
                        # L10 is last column
                        l10_text = stats_cells[-1].get_text().strip()
                        if '-' in l10_text:
                            l10 = l10_text
                    
                    standings_dict[team_name] = {
                        'wins': wins,
                        'losses': losses,
                        'streak': self._format_streak(streak),
                        'l10': l10,
                        'record': f"{wins}-{losses}",
                        'ppg': ppg,
                        'opp_ppg': opp_ppg
                    }
            
            if len(standings_dict) > 0:
                self.nba_cache = standings_dict
                self.cache_time = datetime.now()
                print(f"✅ Scraped NBA standings for {len(standings_dict)} teams from ESPN")
                return standings_dict
            
            return self.nba_cache if self.nba_cache else {}
            
        except ImportError:
            # BeautifulSoup not installed
            print("⚠️  beautifulsoup4 not installed - install with: pip install beautifulsoup4")
            return self.nba_cache if self.nba_cache else {}
        except Exception as e:
            # Fail silently but return cache if available
            return self.nba_cache if self.nba_cache else {}
        finally:
            self._fetching_nba = False
    
    def get_nfl_standings(self) -> Dict[str, Dict]:
        """
        Get NFL standings from ESPN API
        Returns: {team_name: {'wins': int, 'losses': int, 'streak': str, 'l10': str}}
        """
        # Return cached if available and recent (< 5 minutes old)
        if self.nfl_cache and self.cache_time:
            time_diff = (datetime.now() - self.cache_time).total_seconds()
            if time_diff < 300:  # 5 minutes
                return self.nfl_cache
        
        # Prevent concurrent fetches
        if self._fetching_nfl:
            return self.nfl_cache if self.nfl_cache else {}
        
        self._fetching_nfl = True
        try:
            # ESPN API endpoint for NFL standings
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/standings"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️  NFL standings API returned {response.status_code}")
                return self.nfl_cache if self.nfl_cache else {}
            
            data = response.json()
            standings_dict = {}
            
            # Parse ESPN response - structure: children -> divisions -> entries
            for conference in data.get('children', []):
                for division in conference.get('children', []):  # Divisions are children of conferences
                    entries = division.get('standings', {}).get('entries', [])
                    for entry in entries:
                        team = entry.get('team', {})
                        team_name = team.get('displayName', '') or team.get('name', '')
                        
                        if not team_name:
                            continue
                        
                        # Map to our naming convention
                        team_name = self._normalize_nfl_team_name(team_name)
                        
                        stats = entry.get('stats', [])
                        wins = 0
                        losses = 0
                        streak = ''
                        
                        for stat in stats:
                            stat_name = stat.get('name', '')
                            if stat_name == 'wins':
                                wins = int(stat.get('value', 0))
                            elif stat_name == 'losses':
                                losses = int(stat.get('value', 0))
                            elif stat_name == 'streak':
                                streak = stat.get('displayValue', '') or stat.get('value', '')
                        
                        standings_dict[team_name] = {
                            'wins': wins,
                            'losses': losses,
                            'streak': self._format_streak(streak),
                            'l10': 'N/A',  # ESPN doesn't provide L10 easily
                            'record': f"{wins}-{losses}"
                        }
            
            self.nfl_cache = standings_dict
            self.cache_time = datetime.now()
            
            print(f"✅ Fetched NFL standings for {len(standings_dict)} teams")
            return standings_dict
            
        except Exception as e:
            import traceback
            print(f"⚠️  NFL standings fetch failed: {e}")
            traceback.print_exc()
            return self.nfl_cache if self.nfl_cache else {}
        finally:
            self._fetching_nfl = False
    
    def get_team_record(self, team_name: str, sport: str = 'nba') -> Optional[Dict]:
        """Get record for a specific team"""
        if sport.lower() == 'nba':
            standings = self.get_nba_standings()
        else:
            standings = self.get_nfl_standings()
        
        # Try exact match first
        if team_name in standings:
            return standings[team_name]
        
        # Try normalized name
        normalized = StandingsFetcher._normalize_nba_team_name(team_name) if sport == 'nba' else StandingsFetcher._normalize_nfl_team_name(team_name)
        if normalized in standings:
            return standings[normalized]
        
        # Try partial match
        for key, value in standings.items():
            if team_name.lower() in key.lower() or key.lower() in team_name.lower():
                return value
        
        return None
    
    @staticmethod
    def _normalize_nba_team_name(name: str) -> str:
        """Normalize NBA team names to match our convention"""
        # Full name mappings
        full_name_mappings = {
            'Lakers': 'Los Angeles Lakers',
            'Clippers': 'LA Clippers',
            'Knicks': 'New York Knicks',
            'Nets': 'Brooklyn Nets',
            'Warriors': 'Golden State Warriors',
            'Celtics': 'Boston Celtics',
            'Heat': 'Miami Heat',
            'Bulls': 'Chicago Bulls',
            'Mavericks': 'Dallas Mavericks',
            'Suns': 'Phoenix Suns',
            'Wizards': 'Washington Wizards',
            'Hornets': 'Charlotte Hornets',
            'Pistons': 'Detroit Pistons',
            'Raptors': 'Toronto Raptors',
            'Magic': 'Orlando Magic',
            '76ers': 'Philadelphia 76ers',
            'Cavaliers': 'Cleveland Cavaliers',
            'Hawks': 'Atlanta Hawks',
            'Bucks': 'Milwaukee Bucks',
            'Pacers': 'Indiana Pacers',
            'Thunder': 'Oklahoma City Thunder',
            'Nuggets': 'Denver Nuggets',
            'Trail Blazers': 'Portland Trail Blazers',
            'Blazers': 'Portland Trail Blazers',
            'Jazz': 'Utah Jazz',
            'Timberwolves': 'Minnesota Timberwolves',
            'Grizzlies': 'Memphis Grizzlies',
            'Pelicans': 'New Orleans Pelicans',
            'Spurs': 'San Antonio Spurs',
            'Rockets': 'Houston Rockets',
            'Kings': 'Sacramento Kings',
        }
        
        # If already full name, return as-is
        if ' ' in name and len(name) > 10:
            return name
        
        # Try exact match first
        if name in full_name_mappings:
            return full_name_mappings[name]
        
        # Try partial match
        for short, full in full_name_mappings.items():
            if short.lower() in name.lower() or name.lower() in short.lower():
                return full
        
        return name
    
    @staticmethod
    def _normalize_nfl_team_name(name: str) -> str:
        """Normalize NFL team names"""
        # Remove common suffixes
        name = name.replace(' Football Club', '').replace(' FC', '')
        
        # Add city if missing
        if not any(city in name for city in ['New York', 'Los Angeles', 'San Francisco', 'Kansas City']):
            # Most names already have cities, but handle edge cases
            pass
        
        return name
    
    def _format_streak(self, streak_str: str) -> str:
        """Format streak string (e.g., 'W3' or 'L2')"""
        if not streak_str:
            return 'N/A'
        
        streak_str = str(streak_str).strip()
        if streak_str.startswith('W') or streak_str.startswith('L'):
            return streak_str.upper()
        
        # Try to parse if it's in different format
        if 'win' in streak_str.lower():
            num = ''.join(filter(str.isdigit, streak_str))
            return f"W{num}" if num else 'N/A'
        elif 'loss' in streak_str.lower():
            num = ''.join(filter(str.isdigit, streak_str))
            return f"L{num}" if num else 'N/A'
        
        return streak_str

if __name__ == '__main__':
    # Test standings fetcher
    fetcher = StandingsFetcher()
    
    print("\n🏀 Testing NBA Standings...")
    nba_standings = fetcher.get_nba_standings()
    if nba_standings:
        sample_team = list(nba_standings.keys())[0]
        print(f"   Sample: {sample_team} = {nba_standings[sample_team]}")
    
    print("\n🏈 Testing NFL Standings...")
    nfl_standings = fetcher.get_nfl_standings()
    if nfl_standings:
        sample_team = list(nfl_standings.keys())[0]
        print(f"   Sample: {sample_team} = {nfl_standings[sample_team]}")

