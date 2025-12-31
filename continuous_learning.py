#!/usr/bin/env python3
"""
CONTINUOUS LEARNING SYSTEM - Automated Model Retraining
Collect actual results → Update training data → Retrain models → Deploy

Usage:
  python3 continuous_learning.py --full     # Run complete cycle (daily cron)
  python3 continuous_learning.py --collect  # Just collect results
  python3 continuous_learning.py --retrain  # Force retrain
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import subprocess

class ContinuousLearningSystem:
    
    def __init__(self, db_path='predictions.db'):
        self.db_path = db_path
        self.retrain_threshold = 0.05  # Retrain if accuracy drops 5%
        self.min_new_games = 10
        
    def collect_actual_results_from_api(self):
        """Fetch actual game results and update database"""
        from predict_today import ESPNAPI
        
        print("\n📥 Collecting actual game results...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, sport, date, home_team, away_team, 
                   predicted_winner, predicted_spread
            FROM predictions 
            WHERE actual_winner IS NULL 
            AND date >= date('now', '-7 days')
            AND date <= date('now')
        """)
        
        pending = cursor.fetchall()
        print(f"   Found {len(pending)} pending predictions")
        
        updated_count = 0
        
        for pred_id, sport, game_date, home_team, away_team, pred_winner, pred_spread in pending:
            try:
                if sport == 'NFL':
                    scoreboard = ESPNAPI.get_scoreboard(
                        sport='football', league='nfl',
                        dates=game_date.replace('-', '')
                    )
                elif sport == 'NBA':
                    scoreboard = ESPNAPI.get_scoreboard(
                        sport='basketball', league='nba',
                        dates=game_date.replace('-', '')
                    )
                else:
                    continue
                
                for event in scoreboard.get('events', []):
                    if event['status']['type']['name'] != 'STATUS_FINAL':
                        continue
                    
                    comp = event['competitions'][0]
                    home = comp['competitors'][0] if comp['competitors'][0]['homeAway'] == 'home' else comp['competitors'][1]
                    away = comp['competitors'][1] if comp['competitors'][1]['homeAway'] == 'away' else comp['competitors'][0]
                    
                    if (home['team']['displayName'] == home_team and 
                        away['team']['displayName'] == away_team):
                        
                        home_score = int(home.get('score', 0))
                        away_score = int(away.get('score', 0))
                        actual_spread = home_score - away_score
                        actual_winner = home_team if actual_spread > 0 else away_team
                        
                        winner_correct = 1 if actual_winner == pred_winner else 0
                        spread_error = abs(pred_spread - actual_spread)
                        spread_within_7 = 1 if spread_error <= 7 else 0
                        
                        cursor.execute("""
                            UPDATE predictions 
                            SET actual_winner = ?, actual_spread = ?,
                                home_score = ?, away_score = ?,
                                winner_correct = ?, spread_error = ?,
                                spread_within_7 = ?, result_updated_at = ?
                            WHERE id = ?
                        """, (actual_winner, actual_spread, home_score, away_score,
                             winner_correct, spread_error, spread_within_7,
                             datetime.now().isoformat(), pred_id))
                        
                        updated_count += 1
                        status = "✅" if winner_correct else "❌"
                        print(f"   {status} {away_team} @ {home_team}: {actual_winner} by {abs(actual_spread)}")
                        break
                
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Updated {updated_count} predictions")
        return updated_count
    
    def calculate_recent_performance(self, days=30):
        """Calculate accuracy over recent period"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query(f"""
            SELECT sport, COUNT(*) as total, AVG(winner_correct) as accuracy
            FROM predictions
            WHERE actual_winner IS NOT NULL
            AND date >= date('now', '-{days} days')
            GROUP BY sport
        """, conn)
        
        conn.close()
        return df
    
    def retrain_models(self):
        """Retrain with new data"""
        print("\n🔄 Retraining models...")
        
        conn = sqlite3.connect(self.db_path)
        new_data = pd.read_sql_query("""
            SELECT date, sport, home_team, away_team, home_score, away_score
            FROM predictions
            WHERE actual_winner IS NOT NULL AND home_score IS NOT NULL
            ORDER BY date
        """, conn)
        conn.close()
        
        if len(new_data) == 0:
            print("⚠️  No new data")
            return False
        
        nfl_new = new_data[new_data['sport'] == 'NFL']
        
        if len(nfl_new) > 0:
            # Try to update existing data files
            data_paths = [
                Path('data/nfl_2024_raw.csv'),
                Path('data/nfl_2023_2024_features.csv')
            ]
            
            for data_path in data_paths:
                if data_path.exists():
                    try:
                        historical = pd.read_csv(data_path)
                        # Ensure date column exists
                        if 'date' in historical.columns:
                            combined = pd.concat([historical, nfl_new], ignore_index=True)
                            combined = combined.drop_duplicates(subset=['date', 'home_team', 'away_team'], keep='last')
                            combined.to_csv(data_path, index=False)
                            print(f"   ✅ Updated {data_path.name}: Added {len(nfl_new)} games → Total: {len(combined)}")
                    except Exception as e:
                        print(f"   ⚠️  Could not update {data_path}: {e}")
        
        # Retrain models
        result = subprocess.run(
            ['python3', 'enhanced_system_fixed.py', '--train', '--years', '2023,2024'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("   ✅ Models retrained!")
            return True
        else:
            print("   ❌ Retraining failed")
            return False
    
    def run_full_cycle(self):
        """Run complete learning cycle"""
        print("="*80)
        print("🔄 CONTINUOUS LEARNING CYCLE")
        print("="*80)
        
        updated = self.collect_actual_results_from_api()
        
        if updated == 0:
            print("\n⚠️  No new results")
            return
        
        perf = self.calculate_recent_performance()
        print("\n📊 Recent Performance:")
        print(perf.to_string(index=False))
        
        needs_retrain = len(perf[perf['total'] >= self.min_new_games]) > 0
        
        if needs_retrain:
            self.retrain_models()
        else:
            print("\n✅ Not enough new data for retraining")
        
        print("\n" + "="*80)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--collect', action='store_true')
    parser.add_argument('--retrain', action='store_true')
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    
    cls = ContinuousLearningSystem()
    
    if args.collect:
        cls.collect_actual_results_from_api()
    elif args.retrain:
        cls.retrain_models()
    else:
        cls.run_full_cycle()

if __name__ == '__main__':
    main()
