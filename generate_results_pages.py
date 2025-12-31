#!/usr/bin/env python3
"""
Generate Results Pages - Automated Validation Dashboard
Creates HTML pages showing prediction results and performance
"""

from automated_validation_system import AutomatedValidationSystem
from datetime import datetime, timedelta
from pathlib import Path

def generate_results_page():
    """Generate results.html showing recent predictions vs outcomes"""
    
    system = AutomatedValidationSystem()
    df = system.get_recent_results(days=7)
    
    if len(df) == 0:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Recent Results - Pro Sports Intel AI™</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', Arial, sans-serif; 
                       max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
                .empty-state { text-align: center; padding: 60px 20px; color: #86868b; }
            </style>
        </head>
        <body>
            <h1>Recent Results</h1>
            <div class="empty-state">
                <p>No results available yet. Check back after games complete!</p>
            </div>
        </body>
        </html>
        """
    else:
        # Calculate stats
        total = len(df)
        correct = df['was_correct'].sum()
        win_rate = (correct / total * 100) if total > 0 else 0
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recent Results - Pro Sports Intel AI™</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: -2px;
        }}
        
        .subtitle {{
            color: #86868b;
            margin-bottom: 40px;
        }}
        
        .stats-card {{
            background: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        
        .big-stat {{
            font-size: 4rem;
            font-weight: 700;
            color: #34c759;
            margin-bottom: 8px;
        }}
        
        .game-card {{
            background: white;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 16px;
            border-left: 4px solid #e5e5e7;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        
        .game-card.correct {{
            border-left-color: #34c759;
        }}
        
        .game-card.incorrect {{
            border-left-color: #ff3b30;
        }}
        
        .game-card.high-confidence {{
            background: #f0f9ff;
        }}
        
        .game-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}
        
        .game-title {{
            font-size: 1.2rem;
            font-weight: 700;
        }}
        
        .result-badge {{
            padding: 8px 16px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 0.9rem;
        }}
        
        .result-badge.correct {{
            background: #34c759;
            color: white;
        }}
        
        .result-badge.incorrect {{
            background: #ff3b30;
            color: white;
        }}
        
        .score {{
            font-size: 2rem;
            font-weight: 700;
            margin: 12px 0;
        }}
        
        .prediction-info {{
            color: #86868b;
            font-size: 0.9rem;
            margin-top: 12px;
        }}
        
        .divergence {{
            display: inline-block;
            padding: 4px 8px;
            background: #f5f5f7;
            border-radius: 8px;
            font-size: 0.8rem;
            margin-left: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Recent Results</h1>
        <div class="subtitle">Last 7 Days Performance</div>
        
        <div class="stats-card">
            <div class="big-stat">{win_rate:.1f}%</div>
            <p>Win Rate ({correct}/{total} predictions)</p>
        </div>
"""
        
        # Add game cards
        for _, row in df.iterrows():
            was_correct = row['was_correct'] == 1
            is_high_conf = row.get('is_high_confidence', 0) == 1
            
            card_class = 'correct' if was_correct else 'incorrect'
            if is_high_conf:
                card_class += ' high-confidence'
            
            result_badge_class = 'correct' if was_correct else 'incorrect'
            result_text = '✓ CORRECT' if was_correct else '✗ WRONG'
            
            divergence_html = ""
            if row.get('divergence') is not None:
                div = row['divergence']
                divergence_html = f'<span class="divergence">vs Vegas: {div:.1f} pts</span>'
            
            html += f"""
        <div class="game-card {card_class}">
            <div class="game-header">
                <div>
                    <div class="game-title">{row['sport']} - {row['date']}</div>
                    <div class="score">
                        {row['home_team']} {int(row['actual_home_score'])} - {int(row['actual_away_score'])} {row['away_team']}
                    </div>
                </div>
                <div class="result-badge {result_badge_class}">{result_text}</div>
            </div>
            <div class="prediction-info">
                Model predicted: <strong>{row['predicted_winner']}</strong> by {abs(row['predicted_spread']):.1f} pts
                {divergence_html}
                <br>
                Confidence: {row['confidence_score']*100:.0f}% | 
                Spread Error: {row['spread_error']:.1f} pts
            </div>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
    
    # Save HTML
    output_path = Path('predictions/results.html')
    output_path.write_text(html)
    print(f"✅ Results page generated: {output_path}")
    return output_path

def generate_historical_performance_page():
    """Generate historical-performance.html with aggregate stats"""
    
    system = AutomatedValidationSystem()
    stats = system.get_performance_stats()
    
    overall = stats['overall']
    by_sport = stats['by_sport']
    by_confidence = stats['by_confidence']
    
    # Handle None values safely
    total = overall.get('total') or 0
    correct = overall.get('correct') or 0
    avg_conf = overall.get('avg_confidence') or 0
    avg_error = overall.get('avg_spread_error') or 0
    
    win_rate = (correct / total * 100) if total > 0 else 0
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historical Performance - Pro Sports Intel AI™</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 40px;
            letter-spacing: -2px;
        }}
        
        .stat-card {{
            background: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        
        .big-stat {{
            font-size: 4rem;
            font-weight: 700;
            color: #34c759;
            margin-bottom: 8px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e5e7;
        }}
        
        th {{
            background: #f5f5f7;
            font-weight: 600;
            color: #86868b;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .good {{ color: #34c759; font-weight: 700; }}
        .bad {{ color: #ff3b30; font-weight: 700; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Historical Model Performance</h1>
        
        <div class="stat-card">
            <h2>Overall Performance</h2>
            <div class="big-stat">{win_rate:.1f}%</div>
            <p>Win Rate ({correct}/{total} predictions)</p>
            <p>Average Confidence: {avg_conf*100:.1f}%</p>
            <p>Average Spread Error: {avg_error:.1f} points</p>
        </div>
        
        <div class="stat-card">
            <h2>Performance by Sport</h2>
            <table>
                <tr>
                    <th>Sport</th>
                    <th>Record</th>
                    <th>Win Rate</th>
                    <th>Avg Confidence</th>
                </tr>
"""
    
    for sport_stat in by_sport:
        sport = sport_stat['sport']
        sport_total = sport_stat.get('total') or 0
        sport_correct = sport_stat.get('correct') or 0
        sport_win_rate = (sport_correct / sport_total * 100) if sport_total > 0 else 0
        sport_conf = (sport_stat.get('avg_confidence') or 0) * 100
        
        color_class = 'good' if sport_win_rate >= 60 else 'bad'
        
        html += f"""
                <tr>
                    <td><strong>{sport}</strong></td>
                    <td>{sport_correct}-{sport_total - sport_correct}</td>
                    <td class="{color_class}">{sport_win_rate:.1f}%</td>
                    <td>{sport_conf:.0f}%</td>
                </tr>
"""
    
    html += """
            </table>
        </div>
        
        <div class="stat-card">
            <h2>Performance by Confidence Level</h2>
            <table>
                <tr>
                    <th>Confidence Range</th>
                    <th>Record</th>
                    <th>Win Rate</th>
                </tr>
"""
    
    for conf_stat in by_confidence:
        conf_level = conf_stat['confidence_level']
        conf_total = conf_stat.get('total') or 0
        conf_correct = conf_stat.get('correct') or 0
        conf_win_rate = (conf_correct / conf_total * 100) if conf_total > 0 else 0
        
        html += f"""
                <tr>
                    <td>{conf_level}</td>
                    <td>{conf_correct}-{conf_total - conf_correct}</td>
                    <td>{conf_win_rate:.1f}%</td>
                </tr>
"""
    
    html += """
            </table>
        </div>
        
    </div>
</body>
</html>
"""
    
    output_path = Path('predictions/historical-performance.html')
    output_path.write_text(html)
    print(f"✅ Historical performance page generated: {output_path}")
    return output_path

def generate_all_results_pages():
    """Generate all results pages"""
    print("="*80)
    print("📄 GENERATING RESULTS PAGES")
    print("="*80)
    
    generate_results_page()
    generate_historical_performance_page()
    
    print("\n✅ All results pages generated!")

if __name__ == '__main__':
    generate_all_results_pages()

