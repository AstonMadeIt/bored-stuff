#!/usr/bin/env python3
"""
Backfill NBA Results - Populate database with 2024-25 season data
Fetches all completed NBA games and stores them for clutch analysis
"""

import requests
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import time

def fetch_nba_season_games():
    """Fetch all completed NBA games from 2024-25 season"""
    
    print("="*80)
    print("📥 BACKFILLING NBA SEASON DATA")
    print("="*80)
    print("")
    
    # NBA season typically runs Oct - April
    # Start from October 2024
    start_date = datetime(2024, 10, 1)
    end_date = datetime.now()
    
    all_games = []
    current_date = start_date
    
    print(f"Fetching games from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    print("")
    
    # Team name normalization mapping
    TEAM_NAME_MAP = {
        'LA Clippers': 'Los Angeles Clippers',
        'LA Lakers': 'Los Angeles Lakers',
    }
    
    def normalize_team_name(name):
        return TEAM_NAME_MAP.get(name, name)
    
    days_processed = 0
    games_found = 0
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y%m%d')
        
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            response = requests.get(url, params={'dates': date_str}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                
                for event in events:
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
                            
                            if home_score > 0 or away_score > 0:  # Valid game
                                game_data = {
                                    'date': current_date.strftime('%Y-%m-%d'),
                                    'sport': 'NBA',
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'home_score': home_score,
                                    'away_score': away_score,
                                    'actual_winner': home_team if home_score > away_score else away_team,
                                    'actual_spread': home_score - away_score,
                                    'actual_total': home_score + away_score,
                                    'game_id': event.get('id')
                                }
                                
                                # Try to fetch quarter scores from boxscore
                                try:
                                    game_id = event.get('id')
                                    if game_id:
                                        boxscore_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard/{game_id}"
                                        boxscore_response = requests.get(boxscore_url, timeout=5)
                                        
                                        if boxscore_response.status_code == 200:
                                            boxscore_data = boxscore_response.json()
                                            comps = boxscore_data.get('competitions', [])
                                            if comps:
                                                competitors = comps[0].get('competitors', [])
                                                
                                                home_q4 = None
                                                away_q4 = None
                                                
                                                for comp in competitors:
                                                    linescores = comp.get('linescores', [])
                                                    if len(linescores) >= 4:  # Q1-Q4
                                                        is_home = comp.get('homeAway') == 'home'
                                                        prefix = 'home' if is_home else 'away'
                                                        
                                                        game_data[f'{prefix}_q1_score'] = int(linescores[0].get('value', 0))
                                                        game_data[f'{prefix}_q2_score'] = int(linescores[1].get('value', 0))
                                                        game_data[f'{prefix}_q3_score'] = int(linescores[2].get('value', 0))
                                                        game_data[f'{prefix}_q4_score'] = int(linescores[3].get('value', 0))
                                                        
                                                        # Store Q4 scores for differential calculation
                                                        if is_home:
                                                            home_q4 = int(linescores[3].get('value', 0))
                                                        else:
                                                            away_q4 = int(linescores[3].get('value', 0))
                                                
                                                # Calculate Q4 differential if we have both
                                                if home_q4 is not None and away_q4 is not None:
                                                    game_data['home_q4_differential'] = home_q4 - away_q4
                                        
                                        # Small delay to avoid rate limiting
                                        time.sleep(0.05)
                                        
                                except Exception as e:
                                    # If quarter scores fail, continue without them
                                    pass
                                
                                all_games.append(game_data)
                                games_found += 1
                
                if events:
                    days_processed += 1
                    if days_processed % 30 == 0:
                        print(f"   Processed {days_processed} days, found {games_found} games...")
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            print(f"   ⚠️  Error fetching {date_str}: {e}")
        
        current_date += timedelta(days=1)
    
    print("")
    print(f"✅ Found {len(all_games)} completed NBA games")
    return all_games

def store_games_in_database(games):
    """Store games in validation database"""
    
    from automated_validation_system import AutomatedValidationSystem
    
    system = AutomatedValidationSystem()
    conn = sqlite3.connect(system.db_path)
    cursor = conn.cursor()
    
    stored = 0
    skipped = 0
    
    print("")
    print("💾 Storing games in database...")
    
    for game in games:
        try:
            # Check if game already exists
            cursor.execute('''
                SELECT id FROM predictions
                WHERE date = ? AND sport = ? AND home_team = ? AND away_team = ?
            ''', (game['date'], game['sport'], game['home_team'], game['away_team']))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record with results AND Q4 data
                q1_home = game.get('home_q1_score')
                q2_home = game.get('home_q2_score')
                q3_home = game.get('home_q3_score')
                q4_home = game.get('home_q4_score')
                q1_away = game.get('away_q1_score')
                q2_away = game.get('away_q2_score')
                q3_away = game.get('away_q3_score')
                q4_away = game.get('away_q4_score')
                
                # Calculate Q4 differential and clutch indicators
                q4_diff = game.get('home_q4_differential')
                entered_q4_leading = None
                blown_lead = None
                comeback_win = None
                
                # Calculate score after Q3 and clutch indicators
                if q1_home is not None and q2_home is not None and q3_home is not None and \
                   q1_away is not None and q2_away is not None and q3_away is not None:
                    home_after_q3 = q1_home + q2_home + q3_home
                    away_after_q3 = q1_away + q2_away + q3_away
                    entered_q4_leading = 1 if home_after_q3 > away_after_q3 else 0
                    
                    # Blown lead: led after Q3 but lost
                    if entered_q4_leading == 1 and game['home_score'] < game['away_score']:
                        blown_lead = 1
                    else:
                        blown_lead = 0
                    
                    # Comeback win: trailed after Q3 but won
                    if entered_q4_leading == 0 and game['home_score'] > game['away_score']:
                        comeback_win = 1
                    else:
                        comeback_win = 0
                
                cursor.execute('''
                    UPDATE predictions
                    SET actual_home_score = ?,
                        actual_away_score = ?,
                        actual_winner = ?,
                        actual_spread = ?,
                        actual_total = ?,
                        home_q1_score = ?,
                        home_q2_score = ?,
                        home_q3_score = ?,
                        home_q4_score = ?,
                        away_q1_score = ?,
                        away_q2_score = ?,
                        away_q3_score = ?,
                        away_q4_score = ?,
                        home_q4_differential = ?,
                        home_entered_q4_leading = ?,
                        home_blown_lead = ?,
                        home_comeback_win = ?,
                        result_updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    game['home_score'],
                    game['away_score'],
                    game['actual_winner'],
                    game['actual_spread'],
                    game['actual_total'],
                    q1_home,
                    q2_home,
                    q3_home,
                    q4_home,
                    q1_away,
                    q2_away,
                    q3_away,
                    q4_away,
                    q4_diff,
                    entered_q4_leading,
                    blown_lead,
                    comeback_win,
                    existing[0]
                ))
                stored += 1
            else:
                # Insert new record (prediction may not exist yet)
                # Include quarter scores if available
                q1_home = game.get('home_q1_score')
                q2_home = game.get('home_q2_score')
                q3_home = game.get('home_q3_score')
                q4_home = game.get('home_q4_score')
                q1_away = game.get('away_q1_score')
                q2_away = game.get('away_q2_score')
                q3_away = game.get('away_q3_score')
                q4_away = game.get('away_q4_score')
                
                # Calculate Q4 differential and clutch indicators
                q4_diff = game.get('home_q4_differential')  # Already calculated in fetch
                entered_q4_leading = None
                blown_lead = None
                comeback_win = None
                
                # Calculate score after Q3 and clutch indicators
                if q1_home is not None and q2_home is not None and q3_home is not None and \
                   q1_away is not None and q2_away is not None and q3_away is not None:
                    home_after_q3 = q1_home + q2_home + q3_home
                    away_after_q3 = q1_away + q2_away + q3_away
                    entered_q4_leading = 1 if home_after_q3 > away_after_q3 else 0
                    
                    # Blown lead: led after Q3 but lost
                    if entered_q4_leading == 1 and game['home_score'] < game['away_score']:
                        blown_lead = 1
                    else:
                        blown_lead = 0
                    
                    # Comeback win: down after Q3 but won
                    if entered_q4_leading == 0 and game['home_score'] > game['away_score']:
                        comeback_win = 1
                    else:
                        comeback_win = 0
                
                cursor.execute('''
                    INSERT INTO predictions
                    (date, sport, home_team, away_team,
                     actual_home_score, actual_away_score, actual_winner,
                     actual_spread, actual_total,
                     home_q1_score, home_q2_score, home_q3_score, home_q4_score,
                     away_q1_score, away_q2_score, away_q3_score, away_q4_score,
                     home_q4_differential, home_entered_q4_leading,
                     home_blown_lead, home_comeback_win,
                     result_updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    game['date'],
                    game['sport'],
                    game['home_team'],
                    game['away_team'],
                    game['home_score'],
                    game['away_score'],
                    game['actual_winner'],
                    game['actual_spread'],
                    game['actual_total'],
                    q1_home, q2_home, q3_home, q4_home,
                    q1_away, q2_away, q3_away, q4_away,
                    q4_diff, entered_q4_leading, blown_lead, comeback_win
                ))
                stored += 1
                
        except Exception as e:
            skipped += 1
            if skipped <= 5:  # Only print first few errors
                print(f"   ⚠️  Error storing game: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ Stored {stored} games ({skipped} skipped)")
    return stored

def main():
    """Main backfill process"""
    
    print("🚀 Starting NBA season backfill...")
    print("")
    print("This will fetch all completed games from the 2024-25 NBA season")
    print("and populate the database for clutch analysis.")
    print("")
    
    # Fetch all games
    games = fetch_nba_season_games()
    
    if not games:
        print("❌ No games found to backfill")
        return
    
    # Store in database
    stored = store_games_in_database(games)
    
    print("")
    print("="*80)
    print(f"✅ BACKFILL COMPLETE!")
    print(f"   Stored {stored} games in database")
    print("")
    print("🎯 Clutch Analyzer now has data to work with!")
    print("="*80)

if __name__ == '__main__':
    main()

