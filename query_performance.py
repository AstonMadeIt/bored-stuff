#!/usr/bin/env python3
"""
Query Performance - Analyze Model Performance
Query the database to see what games the model predicts best
"""

from automated_validation_system import AutomatedValidationSystem
import pandas as pd
from datetime import datetime, timedelta

def analyze_performance():
    """Analyze model performance across different dimensions"""
    
    system = AutomatedValidationSystem()
    
    print("="*80)
    print("📊 MODEL PERFORMANCE ANALYSIS")
    print("="*80)
    print("")
    
    # Get all completed predictions
    import sqlite3
    conn = sqlite3.connect(system.db_path)
    df = pd.read_sql_query('''
        SELECT 
            sport,
            home_team,
            away_team,
            predicted_winner,
            actual_winner,
            was_correct,
            confidence_score,
            is_high_confidence,
            spread_error,
            divergence,
            date
        FROM predictions
        WHERE actual_winner IS NOT NULL
        ORDER BY date DESC
    ''', conn)
    conn.close()
    
    if len(df) == 0:
        print("⚠️  No completed predictions yet. Check back after games complete!")
        return
    
    total = len(df)
    correct = df['was_correct'].sum()
    win_rate = (correct / total * 100) if total > 0 else 0
    
    print(f"📈 Overall Performance: {correct}/{total} ({win_rate:.1f}%)")
    print("")
    
    # Performance by Sport
    print("🏀🏈 Performance by Sport:")
    print("-" * 60)
    for sport in df['sport'].unique():
        sport_df = df[df['sport'] == sport]
        sport_total = len(sport_df)
        sport_correct = sport_df['was_correct'].sum()
        sport_rate = (sport_correct / sport_total * 100) if sport_total > 0 else 0
        print(f"  {sport}: {sport_correct}/{sport_total} ({sport_rate:.1f}%)")
    print("")
    
    # Performance by Confidence Level
    print("🎯 Performance by Confidence Level:")
    print("-" * 60)
    high_conf = df[df['is_high_confidence'] == 1]
    if len(high_conf) > 0:
        hc_total = len(high_conf)
        hc_correct = high_conf['was_correct'].sum()
        hc_rate = (hc_correct / hc_total * 100) if hc_total > 0 else 0
        print(f"  High Confidence: {hc_correct}/{hc_total} ({hc_rate:.1f}%)")
    
    med_conf = df[(df['is_high_confidence'] == 0) & (df['confidence_score'] >= 0.6)]
    if len(med_conf) > 0:
        mc_total = len(med_conf)
        mc_correct = med_conf['was_correct'].sum()
        mc_rate = (mc_correct / mc_total * 100) if mc_total > 0 else 0
        print(f"  Medium Confidence: {mc_correct}/{mc_total} ({mc_rate:.1f}%)")
    
    low_conf = df[df['confidence_score'] < 0.6]
    if len(low_conf) > 0:
        lc_total = len(low_conf)
        lc_correct = low_conf['was_correct'].sum()
        lc_rate = (lc_correct / lc_total * 100) if lc_total > 0 else 0
        print(f"  Low Confidence: {lc_correct}/{lc_total} ({lc_rate:.1f}%)")
    print("")
    
    # Performance by Divergence (vs Vegas)
    print("💰 Performance by Divergence (vs Vegas):")
    print("-" * 60)
    high_div = df[df['divergence'] >= 6]
    if len(high_div) > 0:
        hd_total = len(high_div)
        hd_correct = high_div['was_correct'].sum()
        hd_rate = (hd_correct / hd_total * 100) if hd_total > 0 else 0
        print(f"  High Divergence (6+ pts): {hd_correct}/{hd_total} ({hd_rate:.1f}%)")
    
    med_div = df[(df['divergence'] >= 3) & (df['divergence'] < 6)]
    if len(med_div) > 0:
        md_total = len(med_div)
        md_correct = med_div['was_correct'].sum()
        md_rate = (md_correct / md_total * 100) if md_total > 0 else 0
        print(f"  Medium Divergence (3-6 pts): {md_correct}/{md_total} ({md_rate:.1f}%)")
    
    low_div = df[df['divergence'] < 3]
    if len(low_div) > 0:
        ld_total = len(low_div)
        ld_correct = low_div['was_correct'].sum()
        ld_rate = (ld_correct / ld_total * 100) if ld_total > 0 else 0
        print(f"  Low Divergence (<3 pts): {ld_correct}/{ld_total} ({ld_rate:.1f}%)")
    print("")
    
    # Best Performing Teams (as predicted winner)
    print("🏆 Best Performing Predictions (by Team):")
    print("-" * 60)
    team_perf = df.groupby('predicted_winner').agg({
        'was_correct': ['sum', 'count', 'mean']
    }).reset_index()
    team_perf.columns = ['team', 'correct', 'total', 'win_rate']
    team_perf = team_perf[team_perf['total'] >= 3].sort_values('win_rate', ascending=False)
    
    for _, row in team_perf.head(10).iterrows():
        print(f"  {row['team']}: {int(row['correct'])}/{int(row['total'])} ({row['win_rate']*100:.1f}%)")
    print("")
    
    # Spread Accuracy
    print("📏 Spread Prediction Accuracy:")
    print("-" * 60)
    avg_error = df['spread_error'].mean()
    within_3 = (df['spread_error'] <= 3).sum()
    within_7 = (df['spread_error'] <= 7).sum()
    print(f"  Average Spread Error: {avg_error:.1f} points")
    print(f"  Within 3 points: {within_3}/{total} ({within_3/total*100:.1f}%)")
    print(f"  Within 7 points: {within_7}/{total} ({within_7/total*100:.1f}%)")
    print("")
    
    # Recent Performance Trend
    print("📅 Recent Performance (Last 7 Days):")
    print("-" * 60)
    recent = df[df['date'] >= (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')]
    if len(recent) > 0:
        recent_total = len(recent)
        recent_correct = recent['was_correct'].sum()
        recent_rate = (recent_correct / recent_total * 100) if recent_total > 0 else 0
        print(f"  Last 7 Days: {recent_correct}/{recent_total} ({recent_rate:.1f}%)")
    else:
        print("  No games in last 7 days")
    print("")
    
    print("="*80)
    print("✅ Analysis complete!")
    print("")
    print("💡 Tips:")
    print("  - High confidence predictions tend to be more reliable")
    print("  - High divergence picks show where model differs from Vegas")
    print("  - Track spread_error to see prediction accuracy")
    print("="*80)

if __name__ == '__main__':
    analyze_performance()

