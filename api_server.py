#!/usr/bin/env python3
"""
REST API Server for NFL Predictions
Production-ready API for serving predictions
"""

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime, timedelta
from database import PredictionDB
from predict_today import predict_todays_games
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from enhanced_system_fixed import ESPNAPI

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

db = PredictionDB()

@app.route('/')
def index():
    """Serve dashboard HTML"""
    try:
        with open('dashboard_template.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Dashboard template not found</h1><p>Create dashboard_template.html</p>", 404

@app.route('/api/predictions/upcoming')
def get_upcoming_predictions():
    """Get upcoming predictions"""
    try:
        sport = request.args.get('sport', None)  # ?sport=NFL or ?sport=NBA
        df = db.get_upcoming_predictions(days_ahead=7, sport=sport)
        return jsonify({
            'success': True,
            'data': df.to_dict('records'),
            'count': len(df),
            'sport': sport or 'ALL'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predictions/high-confidence')
def get_high_confidence_predictions():
    """Get high-confidence predictions only"""
    try:
        df = db.get_upcoming_predictions(days_ahead=7)
        high_conf = df[df['is_high_confidence'] == 1]
        return jsonify({
            'success': True,
            'data': high_conf.to_dict('records'),
            'count': len(high_conf)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/results/completed')
def get_completed_results():
    """Get completed games with predictions"""
    try:
        df = db.get_completed_with_predictions()
        return jsonify({
            'success': True,
            'data': df.to_dict('records'),
            'count': len(df)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/metrics')
def get_metrics():
    """Get performance metrics"""
    try:
        metrics = db.get_latest_metrics()
        if metrics is None:
            return jsonify({
                'success': True,
                'data': {
                    'total_predictions': 0,
                    'accuracy': 0,
                    'high_conf_accuracy': 0,
                    'avg_spread_error': 0
                }
            })
        
        return jsonify({
            'success': True,
            'data': metrics.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predictions/generate', methods=['POST'])
def generate_predictions():
    """Generate predictions for today's games"""
    try:
        sport = request.json.get('sport', 'NFL') if request.is_json else 'NFL'
        
        if sport == 'NBA':
            from nba_predictions import predict_nba_games
            predictions = predict_nba_games()
        else:
            predictions = predict_todays_games()
        
        if predictions.empty:
            return jsonify({
                'success': True,
                'message': f'No {sport} games scheduled for today',
                'count': 0,
                'sport': sport
            })
        
        # Save to database
        saved_count = 0
        for _, pred in predictions.iterrows():
            pred_dict = pred.to_dict()
            pred_dict['sport'] = sport
            db.save_prediction(pred_dict)
            saved_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Generated {saved_count} {sport} predictions',
            'count': saved_count,
            'sport': sport
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/results/update', methods=['POST'])
def update_results():
    """Update game results from ESPN"""
    try:
        # Get recent predictions
        predictions = db.get_upcoming_predictions(days_ahead=3)
        
        updated_count = 0
        for _, pred in predictions.iterrows():
            game_date = pd.to_datetime(pred['game_date'])
            date_str = game_date.strftime('%Y%m%d')
            
            # Check if already has result
            completed = db.get_completed_with_predictions()
            if not completed.empty:
                existing = completed[
                    (completed['game_date'] == pred['game_date']) &
                    (completed['away_team'] == pred['away_team']) &
                    (completed['home_team'] == pred['home_team'])
                ]
                if not existing.empty:
                    continue
            
            # Fetch from ESPN
            games = ESPNAPI.get_scoreboard(dates=date_str)
            
            for event in games.get('events', []):
                if not event['status']['type']['completed']:
                    continue
                
                comp = event['competitions'][0]
                home = comp['competitors'][0] if comp['competitors'][0]['homeAway'] == 'home' else comp['competitors'][1]
                away = comp['competitors'][1] if comp['competitors'][1]['homeAway'] == 'away' else comp['competitors'][0]
                
                home_team = home['team']['displayName']
                away_team = away['team']['displayName']
                
                if (home_team == pred['home_team'] and away_team == pred['away_team']):
                    home_score = int(home.get('score', 0))
                    away_score = int(away.get('score', 0))
                    actual_spread = home_score - away_score
                    actual_winner = home_team if actual_spread > 0 else away_team
                    
                    db.save_result({
                        'date': pred['game_date'],
                        'away_team': away_team,
                        'home_team': home_team,
                        'away_score': away_score,
                        'home_score': home_score,
                        'actual_spread': actual_spread,
                        'actual_winner': actual_winner
                    })
                    updated_count += 1
                    break
        
        # Update metrics
        db.update_metrics()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} game results',
            'count': updated_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("="*80)
    print("🚀 Starting NFL Prediction API Server")
    print("="*80)
    print("\n📡 API Endpoints:")
    print("  GET  /api/predictions/upcoming      - Get upcoming predictions")
    print("  GET  /api/predictions/high-confidence - High-confidence only")
    print("  GET  /api/results/completed         - Completed games")
    print("  GET  /api/metrics                  - Performance metrics")
    print("  POST /api/predictions/generate      - Generate today's predictions")
    print("  POST /api/results/update            - Update game results")
    print("  GET  /health                        - Health check")
    print("\n🌐 Server starting on http://localhost:5000")
    print("="*80)
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Port 5000 is already in use!")
            print("   Kill existing process: lsof -ti:5000 | xargs kill")
            print("   Or use a different port: app.run(port=5001)")
        else:
            raise

