#!/usr/bin/env python3
"""
NBA Clutch Features - Late Game Performance Analysis
Implements the "sales math" formula for NBA predictions:
(Streak × Late Game) / (Record Matchup Divergence - PPG Divergence)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import warnings
warnings.filterwarnings('ignore')

class NBAClutchAnalyzer:
    """Analyze NBA team clutch performance and late game factors"""
    
    def __init__(self):
        self.clutch_cache = {}
        self.cache_time = None
    
    def get_team_clutch_stats(self, team_name, season='2024-25'):
        """
        Calculate clutch/late game statistics for a team
        
        Returns:
        {
            'q4_point_differential': float,  # Average Q4 point diff
            'blown_leads': int,              # Games led 5+ in Q4, lost
            'comeback_wins': int,            # Games down 5+ in Q4, won
            'close_game_record': (wins, losses),  # Record in games <5 points
            'clutch_factor': float,          # Overall clutch score (-10 to +10)
            'late_game_factor': float        # Normalized late game performance
        }
        """
        # Check cache
        cache_key = f"{team_name}_{season}"
        if cache_key in self.clutch_cache and self.cache_time:
            time_diff = (datetime.now() - self.cache_time).total_seconds()
            if time_diff < 3600:  # Cache for 1 hour
                return self.clutch_cache[cache_key]
        
        try:
            # Fetch recent games from ESPN API
            clutch_stats = self._fetch_clutch_stats(team_name)
            self.clutch_cache[cache_key] = clutch_stats
            self.cache_time = datetime.now()
            return clutch_stats
        except Exception as e:
            print(f"   ⚠️  Error calculating clutch stats for {team_name}: {e}")
            # Return neutral defaults
            return {
                'q4_point_differential': 0.0,
                'blown_leads': 0,
                'comeback_wins': 0,
                'close_game_record': (0, 0),
                'clutch_factor': 0.0,
                'late_game_factor': 0.0
            }
    
    def _fetch_clutch_stats(self, team_name):
        """Fetch clutch stats from historical data and ESPN API"""
        try:
            # First try to use our historical data (more reliable)
            clutch_stats = self._calculate_from_historical(team_name)
            if clutch_stats and clutch_stats['clutch_factor'] != 0:
                return clutch_stats
            
            # Fallback to ESPN API if historical data not available
            return self._fetch_from_espn_api(team_name)
            
        except Exception as e:
            print(f"   ⚠️  Error fetching clutch stats: {e}")
            return self._default_clutch_stats()
    
    def _calculate_from_historical(self, team_name):
        """Calculate clutch stats from validation database (has actual results)"""
        try:
            import sqlite3
            import pandas as pd
            
            # Use validation database which has actual game results
            from automated_validation_system import AutomatedValidationSystem
            system = AutomatedValidationSystem()
            conn = sqlite3.connect(system.db_path)
            
            # Get team's completed games with actual scores
            team_name_normalized = team_name.lower()
            
            # Try exact match first, then partial match
            # Normalize team name for matching (handle common variations)
            team_variations = [
                team_name_normalized,
                team_name_normalized.replace('los angeles', 'la'),
                team_name_normalized.replace('la ', 'los angeles '),
            ]
            
            # Build query with OR conditions for variations
            conditions = []
            params = []
            for variation in team_variations:
                conditions.append('(LOWER(home_team) LIKE ? OR LOWER(away_team) LIKE ?)')
                params.extend([f'%{variation}%', f'%{variation}%'])
            
            query = f'''
                SELECT 
                    date, home_team, away_team,
                    actual_home_score, actual_away_score, actual_spread,
                    home_q1_score, home_q2_score, home_q3_score, home_q4_score,
                    away_q1_score, away_q2_score, away_q3_score, away_q4_score,
                    home_q4_differential, home_blown_lead, home_comeback_win,
                    was_correct
                FROM predictions
                WHERE sport = 'NBA'
                  AND actual_home_score IS NOT NULL
                  AND actual_away_score IS NOT NULL
                  AND ({' OR '.join(conditions)})
                ORDER BY date DESC
                LIMIT 20
            '''
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if df.empty:
                return None
            
            # If we have fewer than 5 games, use a simplified calculation
            # based on recent form and game margins
            if len(df) < 5:
                # Use streak and recent performance as proxy
                # Teams on win streaks = positive clutch, loss streaks = negative
                return self._calculate_from_limited_data(df, team_name_normalized)
            
            # Normalize team names
            team_name_normalized = team_name.lower()
            
            # Get team's recent games (last 20)
            # Data is already filtered by SQL query
            team_games = df
            
            if len(team_games) < 5:  # Need at least 5 games
                return None
            
            q4_diffs = []
            blown_leads = 0
            comeback_wins = 0
            close_wins = 0
            close_losses = 0
            
            for _, game in team_games.iterrows():
                is_home = str(game['home_team']).lower() == team_name_normalized
                team_score = int(game['actual_home_score']) if is_home else int(game['actual_away_score'])
                opp_score = int(game['actual_away_score']) if is_home else int(game['actual_home_score'])
                team_won = (team_score > opp_score)
                margin = abs(team_score - opp_score)
                
                # Use ACTUAL Q4 data if available
                has_q4_data = pd.notna(game.get('home_q4_score')) and pd.notna(game.get('away_q4_score'))
                
                if has_q4_data:
                    # REAL Q4 SCORES AVAILABLE!
                    team_q4 = int(game['home_q4_score']) if is_home else int(game['away_q4_score'])
                    opp_q4 = int(game['away_q4_score']) if is_home else int(game['home_q4_score'])
                    q4_diff = team_q4 - opp_q4
                    q4_diffs.append(q4_diff)
                    
                    # Use actual blown lead/comeback data if available
                    if is_home:
                        if pd.notna(game.get('home_blown_lead')) and game['home_blown_lead'] == 1:
                            blown_leads += 1
                        if pd.notna(game.get('home_comeback_win')) and game['home_comeback_win'] == 1:
                            comeback_wins += 1
                    else:
                        # For away team, flip the logic
                        if pd.notna(game.get('home_blown_lead')) and game['home_blown_lead'] == 1:
                            # Home blew lead = away had comeback
                            comeback_wins += 1
                        if pd.notna(game.get('home_comeback_win')) and game['home_comeback_win'] == 1:
                            # Home comeback = away blew lead
                            blown_leads += 1
                    
                    # Close games (decided by <5 points)
                    if margin <= 5:
                        if team_won:
                            close_wins += 1
                        else:
                            close_losses += 1
                else:
                    # Fallback: Estimate from final scores (legacy games without Q4 data)
                    if margin <= 5:
                        if team_won:
                            close_wins += 1
                        else:
                            close_losses += 1
                    
                    # Estimate blown leads/comebacks
                    if team_score > opp_score + 8 and not team_won:
                        blown_leads += 1
                    if team_score < opp_score - 8 and team_won:
                        comeback_wins += 1
                    
                    # Estimate Q4 differential
                    if margin <= 10:
                        q4_diff = (team_score - opp_score) if team_won else -(team_score - opp_score)
                    else:
                        if team_won:
                            q4_diff = min(margin * 0.3, 10)
                        else:
                            q4_diff = -min(margin * 0.3, 10)
                    
                    q4_diffs.append(q4_diff)
            
            # Calculate metrics
            q4_avg_diff = np.mean(q4_diffs) if q4_diffs else 0.0
            
            # Clutch factor: combination of comebacks, close wins, blown leads
            clutch_factor = (comeback_wins * 2) + close_wins - (blown_leads * 2) - close_losses
            clutch_factor = max(-10, min(10, clutch_factor))  # Normalize to -10 to +10
            
            # Late game factor: normalized Q4 performance
            late_game_factor = q4_avg_diff / 10.0  # Normalize to roughly -1 to +1
            late_game_factor = max(-1.0, min(1.0, late_game_factor))
            
            return {
                'q4_point_differential': q4_avg_diff,
                'blown_leads': blown_leads,
                'comeback_wins': comeback_wins,
                'close_game_record': (close_wins, close_losses),
                'clutch_factor': clutch_factor,
                'late_game_factor': late_game_factor
            }
            
        except Exception as e:
            print(f"   ⚠️  Error calculating from historical: {e}")
            return None
    
    def _calculate_from_limited_data(self, df, team_name_normalized):
        """Calculate clutch stats from limited data using proxies"""
        try:
            # Calculate win rate in available games
            wins = 0
            total = len(df)
            margins = []
            
            for _, game in df.iterrows():
                is_home = str(game['home_team']).lower() == team_name_normalized
                team_score = int(game['actual_home_score']) if is_home else int(game['actual_away_score'])
                opp_score = int(game['actual_away_score']) if is_home else int(game['actual_home_score'])
                team_won = (team_score > opp_score)
                margin = abs(team_score - opp_score)
                
                if team_won:
                    wins += 1
                
                margins.append(margin)
            
            win_rate = wins / total if total > 0 else 0.5
            
            # Estimate clutch factor from win rate and game margins
            # Teams that win close games = clutch, teams that lose close = not clutch
            avg_margin = sum(margins) / len(margins) if margins else 0
            
            # If team wins but games are close, they're clutch
            # If team loses but games are close, they're not clutch
            if win_rate > 0.6 and avg_margin < 10:
                clutch_factor = 3.0  # Winning close games
            elif win_rate < 0.4 and avg_margin < 10:
                clutch_factor = -3.0  # Losing close games
            elif win_rate > 0.6:
                clutch_factor = 1.0  # Winning but blowouts
            elif win_rate < 0.4:
                clutch_factor = -1.0  # Losing
            else:
                clutch_factor = 0.0  # Neutral
            
            # Late game factor: estimate from win rate and margins
            late_game_factor = (win_rate - 0.5) * 0.5  # Scale to -0.25 to +0.25
            
            return {
                'q4_point_differential': (win_rate - 0.5) * 5.0,  # Estimate
                'blown_leads': 0,  # Can't calculate from limited data
                'comeback_wins': 0,  # Can't calculate from limited data
                'close_game_record': (wins if avg_margin < 10 else 0, total - wins if avg_margin < 10 else 0),
                'clutch_factor': clutch_factor,
                'late_game_factor': late_game_factor
            }
        except Exception as e:
            return None
    
    def _fetch_from_espn_api(self, team_name):
        """Fallback: Fetch clutch stats from ESPN API"""
        try:
            # Use ESPN API to get recent games
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return self._default_clutch_stats()
            
            data = response.json()
            team_id = None
            
            # Find team ID
            for team in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                if team_name.lower() in team.get('team', {}).get('displayName', '').lower():
                    team_id = team.get('team', {}).get('id')
                    break
            
            if not team_id:
                return self._default_clutch_stats()
            
            # Get team schedule/results
            schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
            schedule_response = requests.get(schedule_url, timeout=10)
            
            if schedule_response.status_code != 200:
                return self._default_clutch_stats()
            
            schedule_data = schedule_response.json()
            games = schedule_data.get('events', [])
            
            # Analyze last 20 games for clutch performance
            recent_games = games[:20] if len(games) > 20 else games
            
            q4_diffs = []
            blown_leads = 0
            comeback_wins = 0
            close_wins = 0
            close_losses = 0
            
            for game in recent_games:
                if game.get('status', {}).get('type', {}).get('completed', False):
                    competition = game.get('competitions', [{}])[0]
                    competitors = competition.get('competitors', [])
                    
                    if len(competitors) < 2:
                        continue
                    
                    # Find team's score
                    team_score = None
                    opp_score = None
                    team_won = False
                    
                    for comp in competitors:
                        comp_team = comp.get('team', {}).get('displayName', '')
                        if team_name.lower() in comp_team.lower():
                            team_score = int(comp.get('score', 0))
                            team_won = comp.get('winner', False)
                        else:
                            opp_score = int(comp.get('score', 0))
                    
                    if team_score is None or opp_score is None:
                        continue
                    
                    # Get quarter-by-quarter scores if available
                    # Note: ESPN API may not always have Q-by-Q data
                    # We'll use game flow/play-by-play if available
                    
                    # For now, estimate Q4 performance from game flow
                    # If team won by small margin, likely close game
                    margin = abs(team_score - opp_score)
                    
                    if margin <= 5:
                        if team_won:
                            close_wins += 1
                        else:
                            close_losses += 1
                    
                    # Estimate blown leads (team scored more but lost)
                    # This is a proxy - ideally we'd have Q4 scores
                    if team_score > opp_score + 5 and not team_won:
                        blown_leads += 1
                    
                    # Estimate comebacks (team scored less but won)
                    if team_score < opp_score - 5 and team_won:
                        comeback_wins += 1
                    
                    # Estimate Q4 differential (if close game, assume Q4 was tight)
                    if margin <= 10:
                        # Close game - Q4 likely decided it
                        q4_diff = team_score - opp_score if team_won else -(team_score - opp_score)
                        q4_diffs.append(q4_diff)
            
            # Calculate metrics
            q4_avg_diff = np.mean(q4_diffs) if q4_diffs else 0.0
            
            # Clutch factor: combination of comebacks, close wins, blown leads
            clutch_factor = (comeback_wins * 2) + close_wins - (blown_leads * 2) - close_losses
            clutch_factor = max(-10, min(10, clutch_factor))  # Normalize to -10 to +10
            
            # Late game factor: normalized Q4 performance
            late_game_factor = q4_avg_diff / 10.0  # Normalize to roughly -1 to +1
            late_game_factor = max(-1.0, min(1.0, late_game_factor))
            
            return {
                'q4_point_differential': q4_avg_diff,
                'blown_leads': blown_leads,
                'comeback_wins': comeback_wins,
                'close_game_record': (close_wins, close_losses),
                'clutch_factor': clutch_factor,
                'late_game_factor': late_game_factor
            }
            
        except Exception as e:
            print(f"   ⚠️  Error fetching clutch stats: {e}")
            return self._default_clutch_stats()
    
    def _default_clutch_stats(self):
        """Return neutral clutch stats when data unavailable"""
        return {
            'q4_point_differential': 0.0,
            'blown_leads': 0,
            'comeback_wins': 0,
            'close_game_record': (0, 0),
            'clutch_factor': 0.0,
            'late_game_factor': 0.0
        }
    
    def calculate_clutch_adjustment(self, home_team, away_team, home_streak, away_streak, 
                                   home_record, away_record, home_ppg, away_ppg, vegas_spread=None):
        """
        Calculate clutch adjustment using your formula:
        (Streak × Late Game) / (Record Matchup Divergence - PPG Divergence)
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_streak: Home team current streak (positive = wins, negative = losses)
            away_streak: Away team current streak
            home_record: (wins, losses) tuple
            away_record: (wins, losses) tuple
            home_ppg: Home team points per game
            away_ppg: Away team points per game
            vegas_spread: Vegas spread (if available)
        
        Returns:
            clutch_adjustment: float (adjustment to add to base spread)
        """
        # Get clutch stats for both teams
        home_clutch = self.get_team_clutch_stats(home_team)
        away_clutch = self.get_team_clutch_stats(away_team)
        
        # Calculate net clutch advantage (home - away)
        # Positive = home better in clutch, Negative = away better in clutch
        net_late_game = home_clutch['late_game_factor'] - away_clutch['late_game_factor']
        net_clutch = home_clutch['clutch_factor'] - away_clutch['clutch_factor']
        
        # Use late_game_factor as primary (more reliable)
        late_game_advantage = net_late_game
        
        # Calculate streak advantage
        # Positive = home has better momentum, Negative = away has better momentum
        streak_advantage = home_streak - away_streak
        
        # FIXED FORMULA: Handle sign correctly
        # When both advantages align (both positive or both negative), amplify
        # When they conflict, dampen or let them cancel
        
        # Base clutch adjustment (separate from streak)
        clutch_base_adjustment = late_game_advantage * 0.3  # Scale clutch impact
        
        # Streak adjustment (separate from clutch)
        # Positive streak = momentum boost, negative streak = penalty
        streak_adjustment = streak_advantage * 0.5  # Scale streak impact
        
        # Check if advantages align
        if (late_game_advantage > 0 and streak_advantage > 0) or \
           (late_game_advantage < 0 and streak_advantage < 0):
            # Same direction: amplify (hot streak + clutch OR cold streak + chokers)
            momentum_multiplier = 1.5
        else:
            # Opposite direction: dampen (hot streak but chokers OR cold streak but clutch)
            momentum_multiplier = 0.5
        
        # Combined numerator: clutch + (streak × multiplier)
        numerator = clutch_base_adjustment + (streak_adjustment * momentum_multiplier)
        
        # Denominator: (Record Matchup Divergence - PPG Divergence)
        # Record matchup: difference in win percentage
        home_win_pct = home_record[0] / (home_record[0] + home_record[1]) if (home_record[0] + home_record[1]) > 0 else 0.5
        away_win_pct = away_record[0] / (away_record[0] + away_record[1]) if (away_record[0] + away_record[1]) > 0 else 0.5
        
        record_matchup_divergence = abs(home_win_pct - away_win_pct)
        
        # PPG divergence: difference in scoring
        ppg_divergence = abs(home_ppg - away_ppg) / 10.0  # Normalize to 0-1 scale
        
        # Calculate denominator: (Record Matchup Divergence - PPG Divergence)
        # This contextualizes when clutch matters more (tight matchups) vs less (blowouts)
        denominator = record_matchup_divergence - ppg_divergence
        
        # Avoid division by zero or negative denominator
        # If denominator is very small or negative, use absolute value with minimum
        if abs(denominator) < 0.05:
            denominator = 0.05  # Minimum threshold
        elif denominator < 0:
            # Negative denominator means PPG divergence > record divergence
            # This suggests stats are misleading - use absolute value
            denominator = abs(denominator)
        
        # Calculate adjustment with context scaling
        # Smaller denominator (tight matchup) = clutch matters MORE
        # Larger denominator (mismatch) = clutch matters LESS
        context_scale = 1.0 / (denominator + 0.1)  # Add small epsilon to avoid extreme values
        clutch_adjustment = numerator * context_scale
        
        # Cap adjustment to reasonable range (-10 to +10 points)
        clutch_adjustment = max(-10.0, min(10.0, clutch_adjustment))
        
        return {
            'clutch_adjustment': clutch_adjustment,
            'numerator': numerator,
            'denominator': denominator,
            'late_game_advantage': late_game_advantage,
            'streak_advantage': streak_advantage,
            'record_matchup_divergence': record_matchup_divergence,
            'ppg_divergence': ppg_divergence,
            'home_clutch_factor': home_clutch['clutch_factor'],
            'away_clutch_factor': away_clutch['clutch_factor']
        }

