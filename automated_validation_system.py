#!/usr/bin/env python3
"""
Automated Validation System
Integrates DraftKings client + ESPN API for automated prediction tracking
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import requests
import json
import sys

# Try to import DraftKings client (optional - not required for system to function)
try:
    from draftkings_client import DraftKingsClient
    DK_AVAILABLE = True
except ImportError:
    DK_AVAILABLE = False
    # Silent fail - DraftKings client is optional (ESPN API is used instead)
    DraftKingsClient = None

class AutomatedValidationSystem:
    """Automated system for tracking predictions and validating results"""
    
    def __init__(self, db_path='predictions/validation.db'):
        self.db_path = db_path
        Path(db_path).parent.mkdir(exist_ok=True)
        self.init_database()
        
        # Initialize DraftKings client if available (optional - ESPN API is primary)
        self.dk_client = None
        if DK_AVAILABLE and DraftKingsClient:
            try:
                self.dk_client = DraftKingsClient()
                # Only print if successfully initialized
            except Exception as e:
                # Silent fail - DraftKings is optional, ESPN API is used instead
                pass
    
    def init_database(self):
        """Initialize validation database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced predictions table with validation fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sport TEXT NOT NULL,
                game_id TEXT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                
                -- Model predictions
                predicted_winner TEXT,
                predicted_spread REAL,
                predicted_total REAL,
                confidence_score REAL,
                is_high_confidence INTEGER DEFAULT 0,
                
                -- Vegas lines (from DraftKings or TheOddsAPI)
                vegas_spread REAL,
                vegas_total REAL,
                vegas_moneyline_home REAL,
                vegas_moneyline_away REAL,
                divergence REAL,  -- abs(predicted_spread - vegas_spread)
                
                -- Enhanced features (for analysis)
                rest_advantage REAL,
                home_is_b2b INTEGER,
                away_is_b2b INTEGER,
                net_rating_advantage REAL,
                
                -- Clutch Analyzer features (NBA predictions)
                clutch_analyzer_used INTEGER DEFAULT 0,
                clutch_adjustment REAL,
                late_game_advantage REAL,
                home_clutch_factor REAL,
                away_clutch_factor REAL,
                
                -- Actual results (filled in after game)
                actual_home_score INTEGER,
                actual_away_score INTEGER,
                actual_winner TEXT,
                actual_spread REAL,
                actual_total INTEGER,
                
                -- Quarter scores (for clutch analysis)
                home_q1_score INTEGER,
                home_q2_score INTEGER,
                home_q3_score INTEGER,
                home_q4_score INTEGER,
                away_q1_score INTEGER,
                away_q2_score INTEGER,
                away_q3_score INTEGER,
                away_q4_score INTEGER,
                home_q4_differential REAL,  -- Q4 only point diff
                home_entered_q4_leading INTEGER,  -- 1 if leading after Q3
                home_blown_lead INTEGER,  -- 1 if led after Q3 but lost
                home_comeback_win INTEGER,  -- 1 if down after Q3 but won
                
                -- Validation analysis
                was_correct INTEGER,  -- Did model pick winner?
                spread_error REAL,    -- abs(predicted_spread - actual_spread)
                total_error REAL,     -- abs(predicted_total - actual_total)
                spread_within_3 INTEGER,  -- Was spread within 3 points?
                spread_within_7 INTEGER,  -- Was spread within 7 points?
                
                -- Bet tracking (optional)
                did_bet INTEGER DEFAULT 0,
                bet_type TEXT,  -- 'spread', 'moneyline', 'total', 'parlay'
                bet_amount REAL,
                bet_outcome TEXT,  -- 'win', 'loss', 'push'
                profit_loss REAL,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result_updated_at TIMESTAMP,
                
                UNIQUE(date, sport, home_team, away_team)
            )
        ''')
        
        # Performance summary table (for quick stats)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sport TEXT,
                total_predictions INTEGER,
                correct_predictions INTEGER,
                win_rate REAL,
                avg_confidence REAL,
                avg_spread_error REAL,
                high_confidence_count INTEGER,
                high_confidence_win_rate REAL,
                high_divergence_count INTEGER,
                high_divergence_win_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, sport)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_path}")
    
    def store_predictions(self, predictions_list):
        """Store predictions from generate_all_predictions.py output"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stored_count = 0
        skipped_count = 0
        
        for pred in predictions_list:
            try:
                # Extract data
                date = pred.get('date', datetime.now().isoformat())
                sport = pred.get('sport', 'NFL')
                home_team = pred.get('home_team', '')
                away_team = pred.get('away_team', '')
                predicted_winner = pred.get('predicted_winner', '')
                predicted_spread = pred.get('predicted_spread', 0)
                confidence_score = pred.get('confidence_score', 0.5)
                is_high_confidence = pred.get('is_high_confidence', 0)
                vegas_spread = pred.get('vegas_spread')
                
                # Calculate divergence
                divergence = None
                if vegas_spread is not None:
                    divergence = abs(predicted_spread - vegas_spread)
                
                # Enhanced features
                rest_advantage = pred.get('rest_advantage', 0)
                home_is_b2b = pred.get('home_is_b2b', 0)
                away_is_b2b = pred.get('away_is_b2b', 0)
                net_rating_advantage = pred.get('net_rating_advantage', 0)
                
                # Clutch Analyzer features (NBA only)
                clutch_analyzer_used = 1 if pred.get('clutch_analyzer_used', False) else 0
                clutch_adjustment = pred.get('clutch_adjustment', 0) or 0
                late_game_advantage = pred.get('late_game_advantage', 0) or 0
                home_clutch_factor = pred.get('home_clutch_factor', 0) or 0
                away_clutch_factor = pred.get('away_clutch_factor', 0) or 0
                
                # Insert or update
                cursor.execute('''
                    INSERT OR REPLACE INTO predictions 
                    (date, sport, home_team, away_team, predicted_winner, predicted_spread,
                     confidence_score, is_high_confidence, vegas_spread, divergence,
                     rest_advantage, home_is_b2b, away_is_b2b, net_rating_advantage,
                     clutch_analyzer_used, clutch_adjustment, late_game_advantage,
                     home_clutch_factor, away_clutch_factor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date, sport, home_team, away_team, predicted_winner, predicted_spread,
                    confidence_score, is_high_confidence, vegas_spread, divergence,
                    rest_advantage, home_is_b2b, away_is_b2b, net_rating_advantage,
                    clutch_analyzer_used, clutch_adjustment, late_game_advantage,
                    home_clutch_factor, away_clutch_factor
                ))
                
                stored_count += 1
                
            except sqlite3.IntegrityError:
                skipped_count += 1  # Duplicate
            except Exception as e:
                print(f"   ⚠️  Error storing prediction: {e}")
                skipped_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Stored {stored_count} predictions ({skipped_count} skipped)")
        return stored_count
    
    def fetch_nfl_results(self, date_str=None):
        """Fetch NFL game results from ESPN API"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            params = {'dates': date_str} if date_str else {}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for event in data.get('events', []):
                if event.get('status', {}).get('type', {}).get('completed', False):
                    competition = event.get('competitions', [{}])[0]
                    competitors = competition.get('competitors', [])
                    
                    if len(competitors) >= 2:
                        home = competitors[0] if competitors[0].get('homeAway') == 'home' else competitors[1]
                        away = competitors[1] if competitors[0].get('homeAway') == 'home' else competitors[0]
                        
                        home_team = home.get('team', {}).get('displayName', '')
                        away_team = away.get('team', {}).get('displayName', '')
                        home_score = int(home.get('score', 0))
                        away_score = int(away.get('score', 0))
                        
                        results.append({
                            'date': date_str,
                            'sport': 'NFL',
                            'home_team': home_team,
                            'away_team': away_team,
                            'home_score': home_score,
                            'away_score': away_score,
                            'actual_winner': home_team if home_score > away_score else away_team,
                            'actual_spread': home_score - away_score,
                            'actual_total': home_score + away_score
                        })
            
            return results
            
        except Exception as e:
            print(f"   ⚠️  Error fetching NFL results: {e}")
            return []
    
    def fetch_nba_results(self, date_str=None):
        """Fetch NBA game results from ESPN API"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        # Team name normalization mapping (ESPN -> Database)
        TEAM_NAME_MAP = {
            'LA Clippers': 'Los Angeles Clippers',
            'LA Lakers': 'Los Angeles Lakers',
        }
        
        def normalize_team_name(name):
            return TEAM_NAME_MAP.get(name, name)
        
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            params = {'dates': date_str} if date_str else {}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for event in data.get('events', []):
                if event.get('status', {}).get('type', {}).get('completed', False):
                    competition = event.get('competitions', [{}])[0]
                    competitors = competition.get('competitors', [])
                    
                    if len(competitors) >= 2:
                        home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                        away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                        
                        if home and away:
                            home_team = normalize_team_name(home.get('team', {}).get('displayName', ''))
                            away_team = normalize_team_name(away.get('team', {}).get('displayName', ''))
                            home_score = int(home.get('score', 0))
                            away_score = int(away.get('score', 0))
                            
                            results.append({
                                'date': date_str,
                                'sport': 'NBA',
                                'home_team': home_team,
                                'away_team': away_team,
                                'home_score': home_score,
                                'away_score': away_score,
                                'actual_winner': home_team if home_score > away_score else away_team,
                                'actual_spread': home_score - away_score,
                                'actual_total': home_score + away_score
                            })
            
            return results
            
        except Exception as e:
            print(f"   ⚠️  Error fetching NBA results: {e}")
            return []
    
    def update_results(self, date_str=None):
        """Update predictions with actual game results"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n📊 Updating results for {date_str}...")
        
        # Fetch results for both sports
        nfl_results = self.fetch_nfl_results(date_str.replace('-', ''))
        nba_results = self.fetch_nba_results(date_str.replace('-', ''))
        
        all_results = nfl_results + nba_results
        
        if len(all_results) == 0:
            print("   ⚠️  No completed games found")
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updated_count = 0
        
        for result in all_results:
            try:
                # Find matching prediction
                cursor.execute('''
                    SELECT id, predicted_winner, predicted_spread, predicted_total
                    FROM predictions
                    WHERE date = ? AND sport = ? AND home_team = ? AND away_team = ?
                ''', (date_str, result['sport'], result['home_team'], result['away_team']))
                
                prediction = cursor.fetchone()
                if not prediction:
                    continue
                
                pred_id, predicted_winner, predicted_spread, predicted_total = prediction
                
                # Calculate validation metrics
                was_correct = 1 if predicted_winner == result['actual_winner'] else 0
                spread_error = abs(predicted_spread - result['actual_spread']) if predicted_spread else None
                total_error = abs(predicted_total - result['actual_total']) if predicted_total else None
                spread_within_3 = 1 if spread_error and spread_error <= 3 else 0
                spread_within_7 = 1 if spread_error and spread_error <= 7 else 0
                
                # Update database
                cursor.execute('''
                    UPDATE predictions 
                    SET actual_home_score = ?,
                        actual_away_score = ?,
                        actual_winner = ?,
                        actual_spread = ?,
                        actual_total = ?,
                        was_correct = ?,
                        spread_error = ?,
                        total_error = ?,
                        spread_within_3 = ?,
                        spread_within_7 = ?,
                        result_updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    result['home_score'],
                    result['away_score'],
                    result['actual_winner'],
                    result['actual_spread'],
                    result['actual_total'],
                    was_correct,
                    spread_error,
                    total_error,
                    spread_within_3,
                    spread_within_7,
                    pred_id
                ))
                
                updated_count += 1
                
            except Exception as e:
                print(f"   ⚠️  Error updating result: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Updated {updated_count} predictions with results")
        return updated_count
    
    def calculate_performance_summary(self, date_str=None, sport=None):
        """Calculate and store performance summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        where_clause = "WHERE actual_winner IS NOT NULL"
        params = []
        
        if date_str:
            where_clause += " AND date = ?"
            params.append(date_str)
        
        if sport:
            where_clause += " AND sport = ?"
            params.append(sport)
        
        # Overall stats
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
                AVG(confidence_score) as avg_confidence,
                AVG(spread_error) as avg_spread_error
            FROM predictions
            {where_clause}
        ''', params)
        
        overall = cursor.fetchone()
        total, correct, avg_conf, avg_error = overall
        
        if total == 0:
            conn.close()
            return None
        
        win_rate = (correct / total) if total > 0 else 0
        
        # High confidence stats
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_hc,
                SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_hc
            FROM predictions
            {where_clause} AND is_high_confidence = 1
        ''', params)
        
        hc_total, hc_correct = cursor.fetchone()
        hc_win_rate = (hc_correct / hc_total) if hc_total > 0 else 0
        
        # High divergence stats (6+ points)
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_hd,
                SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_hd
            FROM predictions
            {where_clause} AND ABS(divergence) >= 6
        ''', params)
        
        hd_total, hd_correct = cursor.fetchone()
        hd_win_rate = (hd_correct / hd_total) if hd_total > 0 else 0
        
        # Store summary
        summary_date = date_str or datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT OR REPLACE INTO performance_summary
            (date, sport, total_predictions, correct_predictions, win_rate,
             avg_confidence, avg_spread_error, high_confidence_count,
             high_confidence_win_rate, high_divergence_count, high_divergence_win_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            summary_date, sport, total, correct, win_rate,
            avg_conf or 0, avg_error or 0, hc_total or 0,
            hc_win_rate, hd_total or 0, hd_win_rate
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'date': summary_date,
            'sport': sport,
            'total': total,
            'correct': correct,
            'win_rate': win_rate,
            'avg_confidence': avg_conf,
            'avg_spread_error': avg_error,
            'high_confidence': {'total': hc_total, 'correct': hc_correct, 'win_rate': hc_win_rate},
            'high_divergence': {'total': hd_total, 'correct': hd_correct, 'win_rate': hd_win_rate}
        }
    
    def get_recent_results(self, days=7):
        """Get recent predictions with results"""
        conn = sqlite3.connect(self.db_path)
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        df = pd.read_sql_query('''
            SELECT 
                date, sport, home_team, away_team,
                predicted_winner, predicted_spread, confidence_score, is_high_confidence,
                actual_home_score, actual_away_score, actual_winner, actual_spread,
                was_correct, spread_error, divergence
            FROM predictions
            WHERE date >= ? AND actual_winner IS NOT NULL
            ORDER BY date DESC, sport
        ''', conn, params=(cutoff_date,))
        
        conn.close()
        return df
    
    def get_performance_stats(self):
        """Get overall performance statistics"""
        conn = sqlite3.connect(self.db_path)
        
        # Overall stats
        overall = pd.read_sql_query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
                AVG(confidence_score) as avg_confidence,
                AVG(spread_error) as avg_spread_error
            FROM predictions
            WHERE actual_winner IS NOT NULL
        ''', conn)
        
        # By sport
        by_sport = pd.read_sql_query('''
            SELECT 
                sport,
                COUNT(*) as total,
                SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
                AVG(confidence_score) as avg_confidence
            FROM predictions
            WHERE actual_winner IS NOT NULL
            GROUP BY sport
        ''', conn)
        
        # By confidence level
        by_confidence = pd.read_sql_query('''
            SELECT 
                CASE 
                    WHEN confidence_score >= 0.70 THEN 'High (70%+)'
                    WHEN confidence_score >= 0.60 THEN 'Medium (60-70%)'
                    ELSE 'Low (<60%)'
                END as confidence_level,
                COUNT(*) as total,
                SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM predictions
            WHERE actual_winner IS NOT NULL
            GROUP BY confidence_level
        ''', conn)
        
        conn.close()
        
        return {
            'overall': overall.to_dict('records')[0] if len(overall) > 0 else {},
            'by_sport': by_sport.to_dict('records'),
            'by_confidence': by_confidence.to_dict('records')
        }

if __name__ == '__main__':
    # Test the system
    system = AutomatedValidationSystem()
    
    # Test storing predictions
    print("\n📊 Testing prediction storage...")
    test_predictions = [
        {
            'date': datetime.now().isoformat(),
            'sport': 'NFL',
            'home_team': 'Falcons',
            'away_team': 'Rams',
            'predicted_winner': 'Falcons',
            'predicted_spread': 4.9,
            'confidence_score': 0.66,
            'is_high_confidence': 1,
            'vegas_spread': -7.5,
            'rest_advantage': 2.0
        }
    ]
    
    system.store_predictions(test_predictions)
    
    # Test fetching results
    print("\n📊 Testing result fetching...")
    results = system.fetch_nfl_results()
    print(f"   Found {len(results)} completed NFL games")
    
    # Test performance stats
    print("\n📊 Testing performance stats...")
    stats = system.get_performance_stats()
    print(f"   Overall: {stats['overall']}")

