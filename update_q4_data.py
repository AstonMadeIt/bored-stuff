#!/usr/bin/env python3
"""
Update Q4 Data - Fetch and store quarter scores for existing NBA games
"""

import requests
import sqlite3
import time
from pathlib import Path

def update_q4_scores():
    """Update existing NBA games with Q4 quarter scores"""
    
    db_path = Path(__file__).parent / 'predictions' / 'validation.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all NBA games without Q4 data
    cursor.execute('''
        SELECT id, date, home_team, away_team, game_id
        FROM predictions
        WHERE sport = 'NBA'
          AND actual_home_score IS NOT NULL
          AND home_q4_score IS NULL
        ORDER BY date DESC
    ''')
    
    games_to_update = cursor.fetchall()
    print(f"📊 Found {len(games_to_update)} games to update with Q4 data")
    print("="*60)
    
    updated = 0
    failed = 0
    
    for idx, (game_id, date, home_team, away_team, espn_game_id) in enumerate(games_to_update, 1):
        if idx % 50 == 0:
            print(f"   Processed {idx}/{len(games_to_update)} games...")
        
        if not espn_game_id:
            # Try to find game_id from ESPN API
            try:
                date_str = date.replace('-', '')
                url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
                response = requests.get(url, params={'dates': date_str}, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])
                    
                    for event in events:
                        comps = event.get('competitions', [{}])[0]
                        competitors = comps.get('competitors', [])
                        
                        if len(competitors) >= 2:
                            home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                            away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                            
                            if home and away:
                                event_home = home.get('team', {}).get('displayName', '')
                                event_away = away.get('team', {}).get('displayName', '')
                                
                                if (event_home == home_team and event_away == away_team) or \
                                   (event_home == away_team and event_away == home_team):
                                    espn_game_id = event.get('id')
                                    break
            except:
                pass
        
        if not espn_game_id:
            failed += 1
            continue
        
        # Fetch boxscore
        try:
            boxscore_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard/{espn_game_id}"
            boxscore_response = requests.get(boxscore_url, timeout=5)
            
            if boxscore_response.status_code == 200:
                boxscore_data = boxscore_response.json()
                comps = boxscore_data.get('competitions', [])
                
                if comps:
                    competitors = comps[0].get('competitors', [])
                    
                    home_q1 = home_q2 = home_q3 = home_q4 = None
                    away_q1 = away_q2 = away_q3 = away_q4 = None
                    
                    for comp in competitors:
                        is_home = comp.get('homeAway') == 'home'
                        linescores = comp.get('linescores', [])
                        
                        if len(linescores) >= 4:
                            if is_home:
                                home_q1 = int(linescores[0].get('value', 0))
                                home_q2 = int(linescores[1].get('value', 0))
                                home_q3 = int(linescores[2].get('value', 0))
                                home_q4 = int(linescores[3].get('value', 0))
                            else:
                                away_q1 = int(linescores[0].get('value', 0))
                                away_q2 = int(linescores[1].get('value', 0))
                                away_q3 = int(linescores[2].get('value', 0))
                                away_q4 = int(linescores[3].get('value', 0))
                    
                    if home_q4 is not None and away_q4 is not None:
                        # Calculate Q4 differential and clutch indicators
                        q4_diff = home_q4 - away_q4
                        
                        # Calculate score after Q3
                        if home_q1 is not None and home_q2 is not None and home_q3 is not None and \
                           away_q1 is not None and away_q2 is not None and away_q3 is not None:
                            home_after_q3 = home_q1 + home_q2 + home_q3
                            away_after_q3 = away_q1 + away_q2 + away_q3
                            entered_q4_leading = 1 if home_after_q3 > away_after_q3 else 0
                            
                            # Get final scores
                            cursor.execute('SELECT actual_home_score, actual_away_score FROM predictions WHERE id = ?', (game_id,))
                            final_scores = cursor.fetchone()
                            
                            if final_scores:
                                final_home, final_away = final_scores
                                
                                # Blown lead: led after Q3 but lost
                                blown_lead = 1 if (entered_q4_leading == 1 and final_home < final_away) else 0
                                
                                # Comeback win: trailed after Q3 but won
                                comeback_win = 1 if (entered_q4_leading == 0 and final_home > final_away) else 0
                                
                                # Update database
                                cursor.execute('''
                                    UPDATE predictions
                                    SET home_q1_score = ?,
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
                                        home_comeback_win = ?
                                    WHERE id = ?
                                ''', (
                                    home_q1, home_q2, home_q3, home_q4,
                                    away_q1, away_q2, away_q3, away_q4,
                                    q4_diff, entered_q4_leading, blown_lead, comeback_win,
                                    game_id
                                ))
                                
                                updated += 1
                                
                                if updated % 100 == 0:
                                    conn.commit()
                        else:
                            failed += 1
                    else:
                        failed += 1
                else:
                    failed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
        
        # Rate limiting
        time.sleep(0.05)
    
    conn.commit()
    conn.close()
    
    print("")
    print("="*60)
    print(f"✅ UPDATE COMPLETE!")
    print(f"   Updated: {updated} games")
    print(f"   Failed: {failed} games")
    print("="*60)

if __name__ == '__main__':
    update_q4_scores()

