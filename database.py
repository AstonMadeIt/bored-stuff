#!/usr/bin/env python3
"""
Database Layer for NFL Prediction System
Production-grade data persistence
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import json

class PredictionDB:
    def __init__(self, db_path='predictions.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if old schema exists and migrate
        try:
            cursor.execute("PRAGMA table_info(predictions)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'sport' not in columns:
                # Migrate old schema
                cursor.execute('''
                    ALTER TABLE predictions ADD COLUMN sport TEXT DEFAULT 'NFL'
                ''')
                conn.commit()
        except:
            pass
        
        # Predictions table (supports multiple sports + continuous learning)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT DEFAULT 'NFL',
                game_date TEXT NOT NULL,
                week INTEGER,
                away_team TEXT NOT NULL,
                home_team TEXT NOT NULL,
                predicted_spread REAL,
                predicted_winner TEXT,
                confidence_score REAL,
                is_high_confidence INTEGER,
                vegas_spread REAL,
                model_market_divergence REAL,
                market_movement REAL,
                actual_winner TEXT,
                actual_spread REAL,
                home_score INTEGER,
                away_score INTEGER,
                winner_correct INTEGER,
                spread_error REAL,
                spread_within_7 INTEGER,
                result_updated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sport, game_date, away_team, home_team)
            )
        ''')
        
        # Add columns if they don't exist (for migration)
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN actual_winner TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN actual_spread REAL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN home_score INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN away_score INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN winner_correct INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN spread_error REAL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN spread_within_7 INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN result_updated_at TIMESTAMP")
        except:
            pass
        
        # Results table (actual game outcomes - supports multiple sports)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT DEFAULT 'NFL',
                game_date TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_score INTEGER,
                home_score INTEGER,
                actual_spread REAL,
                actual_winner TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sport, game_date, away_team, home_team)
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_predictions INTEGER,
                correct_predictions INTEGER,
                accuracy REAL,
                high_conf_predictions INTEGER,
                high_conf_correct INTEGER,
                high_conf_accuracy REAL,
                avg_spread_error REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(game_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_teams ON predictions(away_team, home_team)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_date ON results(game_date)')
        
        conn.commit()
        conn.close()
    
    def save_prediction(self, prediction_dict):
        """Save a prediction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO predictions 
                (sport, game_date, week, away_team, home_team, predicted_spread, 
                 predicted_winner, confidence_score, is_high_confidence,
                 vegas_spread, model_market_divergence, market_movement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction_dict.get('sport', 'NFL'),
                prediction_dict['date'],
                prediction_dict.get('week'),
                prediction_dict['away_team'],
                prediction_dict['home_team'],
                prediction_dict['predicted_spread'],
                prediction_dict['predicted_winner'],
                prediction_dict.get('confidence_score', 0),
                prediction_dict.get('is_high_confidence', 0),
                prediction_dict.get('vegas_spread'),
                prediction_dict.get('model_market_divergence'),
                prediction_dict.get('market_movement')
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def save_result(self, result_dict):
        """Save actual game result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO results
                (sport, game_date, away_team, home_team, away_score, home_score,
                 actual_spread, actual_winner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result_dict.get('sport', 'NFL'),
                result_dict['date'],
                result_dict['away_team'],
                result_dict['home_team'],
                result_dict['away_score'],
                result_dict['home_score'],
                result_dict['actual_spread'],
                result_dict['actual_winner']
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_upcoming_predictions(self, days_ahead=7, sport=None):
        """Get upcoming predictions"""
        conn = sqlite3.connect(self.db_path)
        
        cutoff_date = datetime.now().strftime('%Y-%m-%d')
        future_date = (datetime.now() + pd.Timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        if sport:
            query = '''
                SELECT * FROM predictions
                WHERE sport = ? AND game_date >= ? AND game_date <= ?
                ORDER BY is_high_confidence DESC, confidence_score DESC
            '''
            df = pd.read_sql_query(query, conn, params=(sport, cutoff_date, future_date))
        else:
            query = '''
                SELECT * FROM predictions
                WHERE game_date >= ? AND game_date <= ?
                ORDER BY sport, is_high_confidence DESC, confidence_score DESC
            '''
            df = pd.read_sql_query(query, conn, params=(cutoff_date, future_date))
        
        conn.close()
        return df
    
    def get_completed_with_predictions(self, sport=None):
        """Get completed games that have predictions"""
        conn = sqlite3.connect(self.db_path)
        
        if sport:
            query = '''
                SELECT 
                    p.*,
                    r.away_score,
                    r.home_score,
                    r.actual_spread,
                    r.actual_winner,
                    CASE WHEN p.predicted_winner = r.actual_winner THEN 1 ELSE 0 END as prediction_correct,
                    ABS(p.predicted_spread - r.actual_spread) as spread_error
                FROM predictions p
                INNER JOIN results r ON 
                    p.sport = r.sport AND
                    p.game_date = r.game_date AND
                    p.away_team = r.away_team AND
                    p.home_team = r.home_team
                WHERE p.sport = ?
                ORDER BY r.completed_at DESC
            '''
            df = pd.read_sql_query(query, conn, params=(sport,))
        else:
            query = '''
                SELECT 
                    p.*,
                    r.away_score,
                    r.home_score,
                    r.actual_spread,
                    r.actual_winner,
                    CASE WHEN p.predicted_winner = r.actual_winner THEN 1 ELSE 0 END as prediction_correct,
                    ABS(p.predicted_spread - r.actual_spread) as spread_error
                FROM predictions p
                INNER JOIN results r ON 
                    p.sport = r.sport AND
                    p.game_date = r.game_date AND
                    p.away_team = r.away_team AND
                    p.home_team = r.home_team
                ORDER BY r.completed_at DESC
            '''
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def update_metrics(self, date_str=None):
        """Calculate and save daily metrics"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        completed = self.get_completed_with_predictions()
        
        if completed.empty:
            return
        
        total = len(completed)
        correct = completed['prediction_correct'].sum()
        accuracy = (correct / total * 100) if total > 0 else 0
        
        high_conf = completed[completed['is_high_confidence'] == 1]
        high_conf_total = len(high_conf)
        high_conf_correct = high_conf['prediction_correct'].sum() if not high_conf.empty else 0
        high_conf_accuracy = (high_conf_correct / high_conf_total * 100) if high_conf_total > 0 else 0
        
        avg_spread_error = completed['spread_error'].mean() if 'spread_error' in completed.columns else 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO metrics
            (date, total_predictions, correct_predictions, accuracy,
             high_conf_predictions, high_conf_correct, high_conf_accuracy,
             avg_spread_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date_str, total, correct, accuracy,
              high_conf_total, high_conf_correct, high_conf_accuracy,
              avg_spread_error))
        
        conn.commit()
        conn.close()
    
    def get_latest_metrics(self):
        """Get latest performance metrics"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query('''
            SELECT * FROM metrics
            ORDER BY date DESC
            LIMIT 1
        ''', conn)
        
        conn.close()
        return df.iloc[0] if not df.empty else None

