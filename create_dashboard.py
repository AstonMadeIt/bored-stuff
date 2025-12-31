#!/usr/bin/env python3
"""
Create a beautiful HTML dashboard for NFL and NBA predictions
Inspired by modern, responsive design
"""

import json
from pathlib import Path
from datetime import datetime

def create_dashboard():
    """Generate beautiful HTML dashboard"""
    
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
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        timestamp = dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        timestamp = generated_at
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sports Predictions Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #1e293b;
            --dark-light: #334155;
            --light: #f8fafc;
            --text: #0f172a;
            --text-light: #64748b;
            --border: #e2e8f0;
            --shadow: rgba(0, 0, 0, 0.1);
            --shadow-lg: rgba(0, 0, 0, 0.15);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--text);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px var(--shadow-lg);
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            color: var(--text-light);
            font-size: 0.95rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px var(--shadow);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px var(--shadow-lg);
        }}
        
        .stat-card .label {{
            font-size: 0.85rem;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .stat-card .value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
        }}
        
        .sport-section {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px var(--shadow-lg);
        }}
        
        .sport-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--border);
        }}
        
        .sport-title {{
            font-size: 1.8rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .sport-icon {{
            font-size: 2rem;
        }}
        
        .count-badge {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }}
        
        .predictions-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }}
        
        .prediction-card {{
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
            border: 2px solid var(--border);
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .prediction-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        }}
        
        .prediction-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px var(--shadow);
            border-color: var(--primary);
        }}
        
        .prediction-card.high-confidence {{
            border-color: var(--success);
            background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
        }}
        
        .prediction-card.high-confidence::before {{
            background: var(--success);
        }}
        
        .game-matchup {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--text);
        }}
        
        .prediction-details {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .prediction-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }}
        
        .prediction-row:last-child {{
            border-bottom: none;
        }}
        
        .prediction-label {{
            color: var(--text-light);
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        .prediction-value {{
            font-weight: 600;
            color: var(--text);
        }}
        
        .prediction-value.winner {{
            color: var(--primary);
            font-size: 1.05rem;
        }}
        
        .prediction-value.spread {{
            color: var(--secondary);
            font-size: 1.1rem;
        }}
        
        .confidence-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .confidence-badge.high {{
            background: var(--success);
            color: white;
        }}
        
        .confidence-badge.medium {{
            background: var(--warning);
            color: white;
        }}
        
        .confidence-badge.low {{
            background: var(--border);
            color: var(--text);
        }}
        
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-light);
        }}
        
        .empty-state-icon {{
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }}
        
        .empty-state-text {{
            font-size: 1.1rem;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8rem;
            }}
            
            .predictions-grid {{
                grid-template-columns: 1fr;
            }}
            
            .sport-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 480px) {{
            body {{
                padding: 10px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .sport-section {{
                padding: 20px;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏈🏀 Sports Predictions Dashboard</h1>
            <p>Last updated: {timestamp}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">NFL Predictions</div>
                <div class="value">{len(nfl_preds)}</div>
            </div>
            <div class="stat-card">
                <div class="label">NBA Predictions</div>
                <div class="value">{len(nba_preds)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Games</div>
                <div class="value">{len(nfl_preds) + len(nba_preds)}</div>
            </div>
            <div class="stat-card">
                <div class="label">High Confidence</div>
                <div class="value">{sum(1 for p in nfl_preds + nba_preds if p.get('is_high_confidence') or p.get('confidence_score', 0) > 0.7)}</div>
            </div>
        </div>
        
        {render_sport_section('NFL', '🏈', nfl_preds)}
        {render_sport_section('NBA', '🏀', nba_preds)}
    </div>
    
    <script>
        // Auto-refresh every 5 minutes
        setTimeout(() => {{
            location.reload();
        }}, 300000);
    </script>
</body>
</html>"""
    
    # Save HTML
    html_path = Path('predictions/dashboard.html')
    html_path.write_text(html)
    print(f"✅ Dashboard created: {html_path}")
    return html_path

def render_sport_section(sport, icon, predictions):
    """Render a sport section"""
    
    if not predictions:
        return f"""
        <div class="sport-section">
            <div class="sport-header">
                <div class="sport-title">
                    <span class="sport-icon">{icon}</span>
                    <span>{sport} Predictions</span>
                </div>
                <div class="count-badge">0 games</div>
            </div>
            <div class="empty-state">
                <div class="empty-state-icon">{icon}</div>
                <div class="empty-state-text">No {sport} games scheduled</div>
            </div>
        </div>
        """
    
    cards_html = []
    for pred in predictions:
        away = pred.get('away_team', 'TBD')
        home = pred.get('home_team', 'TBD')
        winner = pred.get('predicted_winner', 'TBD')
        spread = float(pred.get('predicted_spread', 0) or 0)
        confidence = float(pred.get('confidence_score', 0) or pred.get('confidence', 0) or 0)
        is_high_conf = pred.get('is_high_confidence', False) or confidence > 0.7
        vegas = pred.get('vegas_spread')
        if vegas:
            vegas = float(vegas)
        
        # Determine confidence level
        if confidence > 0.7:
            conf_class = 'high'
            conf_text = 'High'
        elif confidence > 0.5:
            conf_class = 'medium'
            conf_text = 'Medium'
        else:
            conf_class = 'low'
            conf_text = 'Low'
        
        card_class = 'prediction-card'
        if is_high_conf:
            card_class += ' high-confidence'
        
        card_html = f"""
        <div class="{card_class}">
            <div class="game-matchup">{away} @ {home}</div>
            <div class="prediction-details">
                <div class="prediction-row">
                    <span class="prediction-label">Predicted Winner</span>
                    <span class="prediction-value winner">{winner}</span>
                </div>
                <div class="prediction-row">
                    <span class="prediction-label">Spread</span>
                    <span class="prediction-value spread">{abs(spread):.1f} pts</span>
                </div>
                {f'<div class="prediction-row"><span class="prediction-label">Vegas Line</span><span class="prediction-value">{abs(vegas):.1f} pts</span></div>' if vegas else ''}
                <div class="prediction-row">
                    <span class="prediction-label">Confidence</span>
                    <span class="confidence-badge {conf_class}">{conf_text} ({confidence*100:.0f}%)</span>
                </div>
            </div>
        </div>
        """
        cards_html.append(card_html)
    
    return f"""
    <div class="sport-section">
        <div class="sport-header">
            <div class="sport-title">
                <span class="sport-icon">{icon}</span>
                <span>{sport} Predictions</span>
            </div>
            <div class="count-badge">{len(predictions)} games</div>
        </div>
        <div class="predictions-grid">
            {''.join(cards_html)}
        </div>
    </div>
    """

if __name__ == '__main__':
    create_dashboard()
