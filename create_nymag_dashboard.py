#!/usr/bin/env python3
"""
Create a New York Magazine-styled dashboard
Sophisticated, editorial, clean design
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def load_historical_data():
    """Load historical game data for trend analysis"""
    historical_data = {}
    
    # Load NFL historical data
    nfl_path = Path('data/nfl_2023_2024_features.csv')
    if nfl_path.exists():
        try:
            df_nfl = pd.read_csv(nfl_path)
            if 'date' in df_nfl.columns:
                df_nfl['date'] = pd.to_datetime(df_nfl['date'])
            historical_data['nfl'] = df_nfl
        except Exception as e:
            print(f"⚠️  Could not load NFL historical data: {e}")
    
    # Load NBA historical data
    nba_path = Path('data/nba_2024_features.csv')
    if nba_path.exists():
        try:
            df_nba = pd.read_csv(nba_path)
            if 'date' in df_nba.columns:
                df_nba['date'] = pd.to_datetime(df_nba['date'])
            historical_data['nba'] = df_nba
        except Exception as e:
            print(f"⚠️  Could not load NBA historical data: {e}")
    
    return historical_data

def get_team_trends(historical_df, team_name, game_date, sport='nfl'):
    """Get recent performance trends for a team"""
    if historical_df is None or historical_df.empty:
        return None
    
    try:
        # Filter to team's recent games before this game
        team_games = historical_df[
            ((historical_df['home_team'] == team_name) | (historical_df['away_team'] == team_name)) &
            (pd.to_datetime(historical_df['date']) < pd.to_datetime(game_date))
        ].tail(8).sort_values('date')  # Last 8 games
        
        if len(team_games) < 3:
            return None
        
        # Calculate trends
        points_scored = []
        points_allowed = []
        wins = []
        dates = []
        
        for _, game in team_games.iterrows():
            dates.append(game['date'].strftime('%m/%d') if hasattr(game['date'], 'strftime') else str(game['date'])[:10])
            
            if game['home_team'] == team_name:
                points_scored.append(float(game.get('home_score', 0)))
                points_allowed.append(float(game.get('away_score', 0)))
                wins.append(1 if game.get('home_win', 0) == 1 else 0)
            else:
                points_scored.append(float(game.get('away_score', 0)))
                points_allowed.append(float(game.get('home_score', 0)))
                wins.append(1 if game.get('home_win', 0) == 0 else 0)
        
        # Calculate momentum (recent vs older performance)
        if len(points_scored) >= 4:
            recent_avg = sum(points_scored[-3:]) / 3
            older_avg = sum(points_scored[:-3]) / (len(points_scored) - 3) if len(points_scored) > 3 else recent_avg
            momentum = recent_avg - older_avg
        else:
            momentum = 0
        
        return {
            'dates': dates,
            'points_scored': points_scored,
            'points_allowed': points_allowed,
            'wins': wins,
            'win_rate': sum(wins) / len(wins) if wins else 0,
            'avg_points': sum(points_scored) / len(points_scored) if points_scored else 0,
            'momentum': momentum,
            'trend': 'hot' if momentum > 2 else ('cold' if momentum < -2 else 'neutral')
        }
    except Exception as e:
        return None

def create_nymag_dashboard():
    """Generate NYMag-styled HTML dashboard"""
    
    # Load predictions
    json_path = Path('predictions/all_predictions.json')
    if not json_path.exists():
        print("❌ No predictions found. Run generate_all_predictions.py first")
        return
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    nfl_preds = data.get('nfl', [])
    nba_preds = data.get('nba', [])
    generated_at = data.get('generated_at', datetime.now().isoformat())
    
    # Load historical data for trends
    historical_data = load_historical_data()
    
    # Pre-calculate all team trends for charts
    trend_charts_data = {}
    for pred in nfl_preds + nba_preds:
        away = pred.get('away_team', '')
        home = pred.get('home_team', '')
        game_date = pred.get('date', datetime.now().isoformat())
        sport = 'nfl' if pred in nfl_preds else 'nba'
        hist_df = historical_data.get(sport)
        
        if hist_df is not None:
            chart_id = f"trend_{abs(hash(f'{away}_{home}_{game_date}'))}"
            away_trends = get_team_trends(hist_df, away, game_date, sport)
            home_trends = get_team_trends(hist_df, home, game_date, sport)
            
            if away_trends and home_trends:
                trend_charts_data[chart_id] = {
                    'away': away,
                    'home': home,
                    'away_trends': away_trends,
                    'home_trends': home_trends
                }
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        timestamp = dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        timestamp = generated_at
    
    # Calculate stats
    total_games = len(nfl_preds) + len(nba_preds)
    high_conf_count = sum(1 for p in nfl_preds + nba_preds if p.get('is_high_confidence') or p.get('confidence_score', 0) > 0.7)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sports Intelligence</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --nymag-red: #d32f2f;
            --nymag-black: #1a1a1a;
            --nymag-gray: #666;
            --nymag-light-gray: #f5f5f5;
            --nymag-white: #ffffff;
            --nymag-accent: #2c3e50;
        }}
        
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            background: var(--nymag-white);
            color: var(--nymag-black);
            line-height: 1.6;
            font-size: 16px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        /* Header - NYMag style */
        .header {{
            border-bottom: 3px solid var(--nymag-red);
            padding: 30px 0 20px;
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 3rem;
            font-weight: 700;
            letter-spacing: -1px;
            color: var(--nymag-black);
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        
        .header .subtitle {{
            font-size: 0.9rem;
            color: var(--nymag-gray);
            font-style: italic;
            margin-bottom: 15px;
        }}
        
        .header .timestamp {{
            font-size: 0.85rem;
            color: var(--nymag-gray);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Stats bar - editorial style */
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
            margin-bottom: 50px;
            padding: 30px 0;
            border-top: 1px solid #ddd;
            border-bottom: 1px solid #ddd;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--nymag-red);
            font-family: 'Helvetica Neue', Arial, sans-serif;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--nymag-gray);
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }}
        
        /* Sport sections - magazine layout */
        .sport-section {{
            margin-bottom: 60px;
        }}
        
        .section-header {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--nymag-red);
        }}
        
        .section-title {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--nymag-black);
        }}
        
        .section-count {{
            font-size: 0.9rem;
            color: var(--nymag-gray);
            font-style: italic;
        }}
        
        /* Predictions grid - editorial cards */
        .predictions-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }}
        
        .prediction-card {{
            background: var(--nymag-white);
            border: 1px solid #ddd;
            padding: 25px;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .prediction-card:hover {{
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            border-color: var(--nymag-red);
        }}
        
        .prediction-card.high-confidence {{
            border-left: 4px solid var(--nymag-red);
            background: linear-gradient(to right, #fff5f5 0%, #ffffff 5%);
        }}
        
        /* Team Trends Section */
        .team-trends-section {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #f0f0f0;
        }}
        
        .trend-header {{
            margin-bottom: 12px;
        }}
        
        .trend-label {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            font-size: 0.8rem;
            font-weight: 600;
            color: #86868b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .trend-chart-container {{
            height: 120px;
            margin: 12px 0;
            position: relative;
        }}
        
        .trend-stats {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-top: 12px;
        }}
        
        .trend-stat {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .trend-team-name {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            font-size: 0.75rem;
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 4px;
            text-align: center;
        }}
        
        .trend-indicator {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 12px;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
        }}
        
        .trend-indicator.hot {{
            background: #34c759;
            color: white;
        }}
        
        .trend-indicator.cold {{
            background: #ff3b30;
            color: white;
        }}
        
        .trend-indicator.neutral {{
            background: #e5e5e7;
            color: #86868b;
        }}
        
        .trend-metric {{
            font-size: 0.75rem;
            color: #86868b;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
        }}
        
        .game-matchup {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--nymag-black);
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.4;
        }}
        
        .prediction-details {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .detail-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .detail-row:last-child {{
            border-bottom: none;
        }}
        
        .detail-label {{
            font-size: 0.85rem;
            color: var(--nymag-gray);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }}
        
        .detail-value {{
            font-weight: 600;
            color: var(--nymag-black);
            font-size: 1rem;
        }}
        
        .detail-value.winner {{
            color: var(--nymag-red);
            font-size: 1.1rem;
        }}
        
        .detail-value.spread {{
            color: var(--nymag-accent);
            font-size: 1.15rem;
        }}
        
        .confidence-badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 3px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }}
        
        .confidence-badge.high {{
            background: var(--nymag-red);
            color: white;
        }}
        
        .confidence-badge.medium {{
            background: #ff9800;
            color: white;
        }}
        
        .confidence-badge.low {{
            background: var(--nymag-light-gray);
            color: var(--nymag-gray);
        }}
        
        .empty-state {{
            text-align: center;
            padding: 80px 20px;
            color: var(--nymag-gray);
        }}
        
        .empty-state-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.3;
        }}
        
        .empty-state-text {{
            font-size: 1.1rem;
            font-style: italic;
        }}
        
        /* High confidence highlight */
        .high-conf-banner {{
            background: var(--nymag-red);
            color: white;
            padding: 15px 25px;
            margin-bottom: 30px;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.9rem;
            font-weight: 600;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .predictions-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-bar {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 480px) {{
            .container {{
                padding: 0 15px;
            }}
            
            .header {{
                padding: 20px 0 15px;
            }}
            
            .stats-bar {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Powered By Section - Apple-grade design */
        .powered-by-section {{
            margin-top: 80px;
            padding: 60px 0;
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-top: 1px solid #e0e0e0;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .powered-by-header {{
            text-align: center;
            margin-bottom: 50px;
        }}
        
        .powered-by-title {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #86868b;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }}
        
        .powered-by-subtitle {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            font-size: 0.9rem;
            color: #86868b;
            font-weight: 400;
        }}
        
        .models-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        .model-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid #e5e5e7;
            position: relative;
            overflow: hidden;
        }}
        
        .model-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #007aff, #5856d6);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .model-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            border-color: #007aff;
        }}
        
        .model-card:hover::before {{
            opacity: 1;
        }}
        
        .model-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}
        
        .model-name {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #1d1d1f;
            letter-spacing: -0.3px;
        }}
        
        .model-badge {{
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .model-badge.primary {{
            background: #007aff;
            color: white;
        }}
        
        .model-badge.secondary {{
            background: #5856d6;
            color: white;
        }}
        
        .model-badge.tool {{
            background: #34c759;
            color: white;
        }}
        
        .model-description {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
            font-size: 0.9rem;
            color: #86868b;
            line-height: 1.5;
        }}
        
        .model-stats {{
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #f5f5f7;
            display: flex;
            gap: 16px;
        }}
        
        .model-stat {{
            flex: 1;
        }}
        
        .model-stat-label {{
            font-size: 0.75rem;
            color: #86868b;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        
        .model-stat-value {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #1d1d1f;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
        }}
        
        /* Apple-style radio buttons (for future filtering) */
        .model-toggle {{
            display: none;
        }}
        
        .model-toggle-label {{
            display: inline-flex;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }}
        
        .model-toggle-indicator {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid #d2d2d7;
            margin-right: 8px;
            position: relative;
            transition: all 0.2s ease;
        }}
        
        .model-toggle:checked + .model-toggle-label .model-toggle-indicator {{
            border-color: #007aff;
            background: #007aff;
        }}
        
        .model-toggle:checked + .model-toggle-label .model-toggle-indicator::after {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: white;
        }}
        
        /* Enhanced animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .model-card {{
            animation: fadeInUp 0.6s ease-out;
            animation-fill-mode: both;
        }}
        
        .model-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .model-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .model-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .model-card:nth-child(4) {{ animation-delay: 0.4s; }}
        .model-card:nth-child(5) {{ animation-delay: 0.5s; }}
        .model-card:nth-child(6) {{ animation-delay: 0.6s; }}
        
        /* Enhanced header with gradient */
        .header {{
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            position: relative;
        }}
        
        .header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--nymag-red), transparent);
        }}
        
        /* Smooth scroll */
        html {{
            scroll-behavior: smooth;
        }}
        
        /* Enhanced card shadows */
        .prediction-card {{
            backdrop-filter: blur(10px);
        }}
        
        /* Glassmorphism effect for stats */
        .stats-bar {{
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
        }}
        
        /* Visualization Section */
        .viz-section {{
            margin: 60px 0;
            padding: 40px 0;
            border-top: 1px solid #e5e5e7;
        }}
        
        .viz-header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .viz-title {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            font-size: 1.8rem;
            font-weight: 600;
            color: #1d1d1f;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
        }}
        
        .viz-subtitle {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
            font-size: 0.95rem;
            color: #86868b;
        }}
        
        .viz-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }}
        
        .viz-card {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            border: 1px solid #e5e5e7;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .viz-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }}
        
        .viz-card-title {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 20px;
            letter-spacing: -0.3px;
        }}
        
        .chart-container {{
            position: relative;
            height: 300px;
            margin-top: 20px;
        }}
        
        .chart-container.large {{
            height: 400px;
        }}
        
        .viz-stats {{
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #f5f5f7;
        }}
        
        .viz-stat {{
            text-align: center;
        }}
        
        .viz-stat-value {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #007aff;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
        }}
        
        .viz-stat-label {{
            font-size: 0.85rem;
            color: #86868b;
            margin-top: 4px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
        }}
        
        /* Full-width chart */
        .viz-fullwidth {{
            grid-column: 1 / -1;
        }}
        
        @media (max-width: 768px) {{
            .viz-grid {{
                grid-template-columns: 1fr;
            }}
            
            .chart-container {{
                height: 250px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sports Intelligence</h1>
            <div class="subtitle">Machine Learning Predictions for NFL & NBA</div>
            <div class="timestamp">Last updated: {timestamp}</div>
        </div>
        
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-number">{len(nfl_preds)}</div>
                <div class="stat-label">NFL Games</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(nba_preds)}</div>
                <div class="stat-label">NBA Games</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{total_games}</div>
                <div class="stat-label">Total Predictions</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{high_conf_count}</div>
                <div class="stat-label">High Confidence</div>
            </div>
        </div>
        
        {render_visualizations_section(nfl_preds, nba_preds)}
        
        {render_sport_section('NFL', '🏈', nfl_preds, historical_data.get('nfl'), trend_charts_data)}
        {render_sport_section('NBA', '🏀', nba_preds, historical_data.get('nba'), trend_charts_data)}
        
        {render_powered_by_section()}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        // Auto-refresh every 5 minutes
        setTimeout(() => {{
            location.reload();
        }}, 300000);
        
        // Initialize visualizations
        {generate_chart_scripts(nfl_preds, nba_preds, total_games, high_conf_count)}
        
        // Initialize team trend charts
        {generate_trend_charts_script(trend_charts_data)}
    </script>
</body>
</html>"""
    
    # Save HTML
    html_path = Path('predictions/dashboard.html')
    html_path.write_text(html)
    print(f"✅ NYMag-styled dashboard created: {html_path}")
    return html_path

def render_sport_section(sport, icon, predictions, historical_df=None, trend_charts_data=None):
    """Render a sport section"""
    
    if not predictions:
        return f"""
        <div class="sport-section">
            <div class="section-header">
                <div class="section-title">{icon} {sport}</div>
                <div class="section-count">0 games</div>
            </div>
            <div class="empty-state">
                <div class="empty-state-icon">{icon}</div>
                <div class="empty-state-text">No {sport} games scheduled</div>
            </div>
        </div>
        """
    
    # Separate high confidence games
    high_conf = [p for p in predictions if p.get('is_high_confidence') or p.get('confidence_score', 0) > 0.7]
    regular = [p for p in predictions if not (p.get('is_high_confidence') or p.get('confidence_score', 0) > 0.7)]
    
    cards_html = []
    
    # High confidence banner
    if high_conf:
        cards_html.append(f'<div class="high-conf-banner">🎯 {len(high_conf)} High-Confidence Predictions</div>')
    
    # Render high confidence first
    for pred in high_conf:
        cards_html.append(render_prediction_card(pred, is_high_conf=True, historical_df=historical_df, sport=sport.lower(), trend_charts_data=trend_charts_data))
    
    # Then regular predictions
    for pred in regular:
        cards_html.append(render_prediction_card(pred, is_high_conf=False, historical_df=historical_df, sport=sport.lower(), trend_charts_data=trend_charts_data))
    
    return f"""
    <div class="sport-section">
        <div class="section-header">
            <div class="section-title">{icon} {sport}</div>
            <div class="section-count">{len(predictions)} games</div>
        </div>
        <div class="predictions-grid">
            {''.join(cards_html)}
        </div>
    </div>
    """

def render_prediction_card(pred, is_high_conf=False, historical_df=None, sport='nfl', trend_charts_data=None):
    """Render a single prediction card with team trends"""
    
    away = pred.get('away_team', 'TBD')
    home = pred.get('home_team', 'TBD')
    winner = pred.get('predicted_winner', 'TBD')
    spread = float(pred.get('predicted_spread', 0) or 0)
    confidence = float(pred.get('confidence_score', 0) or pred.get('confidence', 0) or 0)
    vegas = pred.get('vegas_spread')
    game_date = pred.get('date', datetime.now().isoformat())
    
    if vegas:
        vegas = float(vegas)
    
    # Get team trends
    away_trends = get_team_trends(historical_df, away, game_date, sport) if historical_df is not None else None
    home_trends = get_team_trends(historical_df, home, game_date, sport) if historical_df is not None else None
    
    # Generate unique chart ID (must match the one used in trend_charts_data)
    chart_id = f"trend_{abs(hash(f'{away}_{home}_{game_date}'))}"
    
    # Determine confidence level
    if confidence > 0.7 or is_high_conf:
        conf_class = 'high'
        conf_text = 'High'
    elif confidence > 0.5:
        conf_class = 'medium'
        conf_text = 'Medium'
    else:
        conf_class = 'low'
        conf_text = 'Low'
    
    card_class = 'prediction-card'
    if is_high_conf or confidence > 0.7:
        card_class += ' high-confidence'
    
    # Build trend visualization HTML
    trend_html = ""
    if away_trends and home_trends:
        trend_html = f"""
        <div class="team-trends-section">
            <div class="trend-header">
                <span class="trend-label">Recent Form</span>
            </div>
            <div class="trend-chart-container">
                <canvas id="{chart_id}"></canvas>
            </div>
            <div class="trend-stats">
                <div class="trend-stat">
                    <span class="trend-team-name">{away[:12]}</span>
                    <span class="trend-indicator {'hot' if away_trends['trend'] == 'hot' else ('cold' if away_trends['trend'] == 'cold' else 'neutral')}">
                        {away_trends['trend'].upper() if away_trends['trend'] != 'neutral' else 'STABLE'}
                    </span>
                    <span class="trend-metric">{away_trends['avg_points']:.1f} PPG</span>
                </div>
                <div class="trend-stat">
                    <span class="trend-team-name">{home[:12]}</span>
                    <span class="trend-indicator {'hot' if home_trends['trend'] == 'hot' else ('cold' if home_trends['trend'] == 'cold' else 'neutral')}">
                        {home_trends['trend'].upper() if home_trends['trend'] != 'neutral' else 'STABLE'}
                    </span>
                    <span class="trend-metric">{home_trends['avg_points']:.1f} PPG</span>
                </div>
            </div>
        </div>
        """
        
        # Add chart data to script
        trend_data_script = f"""
        """
    
    return f"""
    <div class="{card_class}">
        <div class="game-matchup">{away}<br>@ {home}</div>
        <div class="prediction-details">
            <div class="detail-row">
                <span class="detail-label">Predicted Winner</span>
                <span class="detail-value winner">{winner}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Spread</span>
                <span class="detail-value spread">{abs(spread):.1f} pts</span>
            </div>
            {f'<div class="detail-row"><span class="detail-label">Vegas Line</span><span class="detail-value">{abs(vegas):.1f} pts</span></div>' if vegas else ''}
            <div class="detail-row">
                <span class="detail-label">Confidence</span>
                <span class="confidence-badge {conf_class}">{conf_text} ({confidence*100:.0f}%)</span>
            </div>
        </div>
        {trend_html}
    </div>
    """

def render_visualizations_section(nfl_preds, nba_preds):
    """Render Apple-grade visualizations section"""
    
    # Calculate data for charts
    all_preds = nfl_preds + nba_preds
    
    # Confidence distribution
    conf_levels = {'High': 0, 'Medium': 0, 'Low': 0}
    for p in all_preds:
        conf = p.get('confidence_score', 0) or 0
        if conf > 0.7:
            conf_levels['High'] += 1
        elif conf > 0.5:
            conf_levels['Medium'] += 1
        else:
            conf_levels['Low'] += 1
    
    # Spread distribution
    spreads = [abs(float(p.get('predicted_spread', 0) or 0)) for p in all_preds]
    spread_buckets = {'0-3': 0, '4-7': 0, '8-14': 0, '15+': 0}
    for s in spreads:
        if s <= 3:
            spread_buckets['0-3'] += 1
        elif s <= 7:
            spread_buckets['4-7'] += 1
        elif s <= 14:
            spread_buckets['8-14'] += 1
        else:
            spread_buckets['15+'] += 1
    
    # Sport breakdown
    sport_counts = {'NFL': len(nfl_preds), 'NBA': len(nba_preds)}
    
    # Vegas vs Model comparison (if available)
    vegas_data = []
    model_data = []
    labels = []
    for p in all_preds[:10]:  # Limit to 10 for readability
        if p.get('vegas_spread') is not None:
            labels.append(f"{p.get('away_team', '')[:3]} @ {p.get('home_team', '')[:3]}")
            vegas_data.append(abs(float(p.get('vegas_spread', 0))))
            model_data.append(abs(float(p.get('predicted_spread', 0) or 0)))
    
    return f"""
    <div class="viz-section">
        <div class="viz-header">
            <div class="viz-title">Performance Analytics</div>
            <div class="viz-subtitle">Data-driven insights from our prediction models</div>
        </div>
        
        <div class="viz-grid">
            <!-- Confidence Distribution -->
            <div class="viz-card">
                <div class="viz-card-title">Confidence Distribution</div>
                <div class="chart-container">
                    <canvas id="confidenceChart"></canvas>
                </div>
                <div class="viz-stats">
                    <div class="viz-stat">
                        <div class="viz-stat-value">{conf_levels['High']}</div>
                        <div class="viz-stat-label">High Confidence</div>
                    </div>
                    <div class="viz-stat">
                        <div class="viz-stat-value">{conf_levels['Medium']}</div>
                        <div class="viz-stat-label">Medium</div>
                    </div>
                    <div class="viz-stat">
                        <div class="viz-stat-value">{conf_levels['Low']}</div>
                        <div class="viz-stat-label">Low</div>
                    </div>
                </div>
            </div>
            
            <!-- Spread Distribution -->
            <div class="viz-card">
                <div class="viz-card-title">Predicted Spread Distribution</div>
                <div class="chart-container">
                    <canvas id="spreadChart"></canvas>
                </div>
                <div class="viz-stats">
                    <div class="viz-stat">
                        <div class="viz-stat-value">{spread_buckets['0-3']}</div>
                        <div class="viz-stat-label">Close Games</div>
                    </div>
                    <div class="viz-stat">
                        <div class="viz-stat-value">{spread_buckets['15+']}</div>
                        <div class="viz-stat-label">Blowouts</div>
                    </div>
                </div>
            </div>
            
            <!-- Sport Breakdown -->
            <div class="viz-card">
                <div class="viz-card-title">Predictions by Sport</div>
                <div class="chart-container">
                    <canvas id="sportChart"></canvas>
                </div>
                <div class="viz-stats">
                    <div class="viz-stat">
                        <div class="viz-stat-value">{sport_counts['NFL']}</div>
                        <div class="viz-stat-label">NFL Games</div>
                    </div>
                    <div class="viz-stat">
                        <div class="viz-stat-value">{sport_counts['NBA']}</div>
                        <div class="viz-stat-label">NBA Games</div>
                    </div>
                </div>
            </div>
            
            <!-- Vegas vs Model Comparison -->
            {f'''
            <div class="viz-card viz-fullwidth">
                <div class="viz-card-title">Model vs Vegas Line Comparison</div>
                <div class="chart-container large">
                    <canvas id="vegasChart"></canvas>
                </div>
                <div class="viz-stats">
                    <div class="viz-stat">
                        <div class="viz-stat-value">{len([p for p in all_preds if p.get('vegas_spread')])}</div>
                        <div class="viz-stat-label">Games with Vegas Data</div>
                    </div>
                </div>
            </div>
            ''' if vegas_data else ''}
        </div>
    </div>
    """

def generate_chart_scripts(nfl_preds, nba_preds, total_games, high_conf_count):
    """Generate JavaScript for Chart.js visualizations"""
    
    all_preds = nfl_preds + nba_preds
    
    # Confidence distribution data
    conf_levels = {'High': 0, 'Medium': 0, 'Low': 0}
    for p in all_preds:
        conf = p.get('confidence_score', 0) or 0
        if conf > 0.7:
            conf_levels['High'] += 1
        elif conf > 0.5:
            conf_levels['Medium'] += 1
        else:
            conf_levels['Low'] += 1
    
    # Spread distribution data
    spreads = [abs(float(p.get('predicted_spread', 0) or 0)) for p in all_preds]
    spread_buckets = {'0-3': 0, '4-7': 0, '8-14': 0, '15+': 0}
    for s in spreads:
        if s <= 3:
            spread_buckets['0-3'] += 1
        elif s <= 7:
            spread_buckets['4-7'] += 1
        elif s <= 14:
            spread_buckets['8-14'] += 1
        else:
            spread_buckets['15+'] += 1
    
    # Sport breakdown
    sport_counts = {'NFL': len(nfl_preds), 'NBA': len(nba_preds)}
    
    # Vegas vs Model data
    vegas_data = []
    model_data = []
    labels = []
    for p in all_preds[:10]:
        if p.get('vegas_spread') is not None:
            away_short = (p.get('away_team', '') or '')[:8]
            home_short = (p.get('home_team', '') or '')[:8]
            labels.append(f"{away_short} @ {home_short}")
            vegas_data.append(abs(float(p.get('vegas_spread', 0))))
            model_data.append(abs(float(p.get('predicted_spread', 0) or 0)))
    
    chart_config = {
        'defaultFontFamily': '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif',
        'defaultColor': '#86868b',
        'responsive': True,
        'maintainAspectRatio': False,
        'plugins': {
            'legend': {
                'position': 'bottom',
                'labels': {
                    'font': {'size': 12},
                    'padding': 15,
                    'usePointStyle': True
                }
            },
            'tooltip': {
                'backgroundColor': 'rgba(0,0,0,0.8)',
                'padding': 12,
                'cornerRadius': 8,
                'displayColors': True
            }
        }
    }
    
    return f"""
        // Chart.js configuration
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif';
        Chart.defaults.color = '#86868b';
        
        // Confidence Distribution Chart
        const confCtx = document.getElementById('confidenceChart');
        if (confCtx) {{
            new Chart(confCtx, {{
                type: 'doughnut',
                data: {{
                    labels: ['High', 'Medium', 'Low'],
                    datasets: [{{
                        data: [{conf_levels['High']}, {conf_levels['Medium']}, {conf_levels['Low']}],
                        backgroundColor: ['#007aff', '#ff9500', '#e5e5e7'],
                        borderWidth: 0,
                        hoverOffset: 8
                    }}]
                }},
                options: {{
                    ...{json.dumps(chart_config)},
                    cutout: '60%',
                    plugins: {{
                        ...{json.dumps(chart_config['plugins'])},
                        legend: {{
                            position: 'bottom',
                            labels: {{
                                padding: 12,
                                font: {{ size: 11 }},
                                usePointStyle: true
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // Spread Distribution Chart
        const spreadCtx = document.getElementById('spreadChart');
        if (spreadCtx) {{
            new Chart(spreadCtx, {{
                type: 'bar',
                data: {{
                    labels: ['0-3 pts', '4-7 pts', '8-14 pts', '15+ pts'],
                    datasets: [{{
                        label: 'Number of Games',
                        data: [{spread_buckets['0-3']}, {spread_buckets['4-7']}, {spread_buckets['8-14']}, {spread_buckets['15+']}],
                        backgroundColor: '#007aff',
                        borderRadius: 8,
                        borderSkipped: false
                    }}]
                }},
                options: {{
                    ...{json.dumps(chart_config)},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                stepSize: 1,
                                font: {{ size: 11 }}
                            }},
                            grid: {{
                                color: '#f5f5f7'
                            }}
                        }},
                        x: {{
                            ticks: {{
                                font: {{ size: 11 }}
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }},
                    plugins: {{
                        ...{json.dumps(chart_config['plugins'])},
                        legend: {{
                            display: false
                        }}
                    }}
                }}
            }});
        }}
        
        // Sport Breakdown Chart
        const sportCtx = document.getElementById('sportChart');
        if (sportCtx) {{
            new Chart(sportCtx, {{
                type: 'pie',
                data: {{
                    labels: ['NFL', 'NBA'],
                    datasets: [{{
                        data: [{sport_counts['NFL']}, {sport_counts['NBA']}],
                        backgroundColor: ['#d32f2f', '#ff6b35'],
                        borderWidth: 0,
                        hoverOffset: 8
                    }}]
                }},
                options: {{
                    ...{json.dumps(chart_config)},
                    plugins: {{
                        ...{json.dumps(chart_config['plugins'])},
                        legend: {{
                            position: 'bottom',
                            labels: {{
                                padding: 12,
                                font: {{ size: 11 }},
                                usePointStyle: true
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // Vegas vs Model Comparison
        const vegasCtx = document.getElementById('vegasChart');
        if (vegasCtx && {len(vegas_data)} > 0) {{
            new Chart(vegasCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Vegas Line',
                        data: {json.dumps(vegas_data)},
                        borderColor: '#5856d6',
                        backgroundColor: 'rgba(88, 86, 214, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#5856d6',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }}, {{
                        label: 'Model Prediction',
                        data: {json.dumps(model_data)},
                        borderColor: '#007aff',
                        backgroundColor: 'rgba(0, 122, 255, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#007aff',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }}]
                }},
                options: {{
                    ...{json.dumps(chart_config)},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                font: {{ size: 11 }},
                                callback: function(value) {{
                                    return value + ' pts';
                                }}
                            }},
                            grid: {{
                                color: '#f5f5f7'
                            }}
                        }},
                        x: {{
                            ticks: {{
                                font: {{ size: 10 }},
                                maxRotation: 45,
                                minRotation: 45
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }},
                    plugins: {{
                        ...{json.dumps(chart_config['plugins'])},
                        legend: {{
                            position: 'top',
                            labels: {{
                                padding: 15,
                                font: {{ size: 12 }},
                                usePointStyle: true
                            }}
                        }}
                    }}
                }}
            }});
        }}
    """

def generate_trend_charts_script(trend_charts_data):
    """Generate JavaScript for all team trend charts"""
    
    scripts = []
    for chart_id, data in trend_charts_data.items():
        away = data['away']
        home = data['home']
        away_trends = data['away_trends']
        home_trends = data['home_trends']
        
        script = f"""
        const trendCtx_{chart_id} = document.getElementById('{chart_id}');
        if (trendCtx_{chart_id}) {{
            new Chart(trendCtx_{chart_id}, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(away_trends['dates'])},
                    datasets: [{{
                        label: '{away[:15]}',
                        data: {json.dumps(away_trends['points_scored'])},
                        borderColor: '#007aff',
                        backgroundColor: 'rgba(0, 122, 255, 0.1)',
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                        fill: true
                    }}, {{
                        label: '{home[:15]}',
                        data: {json.dumps(home_trends['points_scored'])},
                        borderColor: '#d32f2f',
                        backgroundColor: 'rgba(211, 47, 47, 0.1)',
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderWidth: 2,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'bottom',
                            labels: {{
                                font: {{ size: 10 }},
                                padding: 8,
                                usePointStyle: true
                            }}
                        }},
                        tooltip: {{
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            padding: 8,
                            cornerRadius: 6,
                            displayColors: true,
                            titleFont: {{ size: 11 }},
                            bodyFont: {{ size: 10 }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: false,
                            ticks: {{
                                font: {{ size: 9 }},
                                stepSize: 5
                            }},
                            grid: {{
                                color: '#f5f5f7'
                            }}
                        }},
                        x: {{
                            ticks: {{
                                font: {{ size: 9 }},
                                maxRotation: 45,
                                minRotation: 45
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }}
                }}
            }});
        }}
        """
        scripts.append(script)
    
    return '\n'.join(scripts)

def render_powered_by_section():
    """Render Apple-grade 'Powered By' section with all models"""
    
    models = [
        {
            'name': 'CatBoost',
            'badge': 'primary',
            'description': 'Gradient boosting on decision trees. Our primary prediction model achieving 62.5% accuracy.',
            'stats': {'Accuracy': '62.5%', 'Type': 'Ensemble'}
        },
        {
            'name': 'XGBoost',
            'badge': 'secondary',
            'description': 'Extreme gradient boosting. Ensemble member providing robust predictions through parallel tree construction.',
            'stats': {'Type': 'Ensemble', 'Speed': 'Fast'}
        },
        {
            'name': 'LightGBM',
            'badge': 'secondary',
            'description': 'Light gradient boosting machine. Fast, distributed gradient boosting framework for high-performance predictions.',
            'stats': {'Type': 'Ensemble', 'Speed': 'Very Fast'}
        },
        {
            'name': 'Optuna',
            'badge': 'tool',
            'description': 'Hyperparameter optimization framework. Automatically tunes model parameters for optimal performance using Bayesian optimization.',
            'stats': {'Type': 'Optimizer', 'Trials': '30+'}
        },
        {
            'name': 'SHAP',
            'badge': 'tool',
            'description': 'SHapley Additive exPlanations. Provides model interpretability by explaining individual predictions.',
            'stats': {'Type': 'Explainability', 'Method': 'Game Theory'}
        },
        {
            'name': 'nfl_data_py',
            'badge': 'tool',
            'description': 'Play-by-play data integration. Real EPA, success rates, and explosive play metrics from NFL play-by-play data.',
            'stats': {'Type': 'Data Source', 'Coverage': '1999+'}
        }
    ]
    
    cards_html = []
    for model in models:
        stats_html = ''.join([
            f'<div class="model-stat"><div class="model-stat-label">{k}</div><div class="model-stat-value">{v}</div></div>'
            for k, v in model['stats'].items()
        ])
        
        cards_html.append(f"""
        <div class="model-card">
            <div class="model-header">
                <div class="model-name">{model['name']}</div>
                <span class="model-badge {model['badge']}">{model['badge'].title()}</span>
            </div>
            <div class="model-description">{model['description']}</div>
            <div class="model-stats">
                {stats_html}
            </div>
        </div>
        """)
    
    return f"""
    <div class="powered-by-section">
        <div class="powered-by-header">
            <div class="powered-by-title">Powered By</div>
            <div class="powered-by-subtitle">Advanced Machine Learning & Data Science</div>
        </div>
        <div class="models-grid">
            {''.join(cards_html)}
        </div>
    </div>
    """

if __name__ == '__main__':
    # Use Apple-grade dashboard
    from create_apple_dashboard import create_apple_dashboard
    create_apple_dashboard()

