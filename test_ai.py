#!/usr/bin/env python3
"""
Quick test to verify AI integration is working
"""

import os
from ai_insights import AIInsightsGenerator

# Check if API key is set
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("❌ ANTHROPIC_API_KEY not set!")
    print("   Run: export ANTHROPIC_API_KEY='your-key'")
    exit(1)

print(f"✅ API key found (length: {len(api_key)})")

# Test AI generation
try:
    generator = AIInsightsGenerator(api_key=api_key)
    
    # Test prediction
    test_prediction = {
        'away_team': 'Milwaukee Bucks',
        'home_team': 'Charlotte Hornets',
        'predicted_winner': 'Charlotte Hornets',
        'predicted_spread': 3.0,
        'confidence_score': 0.73,
        'vegas_spread': 1.5
    }
    
    test_factors = [
        {'icon': '📊', 'text': 'Model sees 1.5 pt edge vs Vegas', 'importance': 'high'},
        {'icon': '📈', 'text': 'Home team on upward trend', 'importance': 'medium'}
    ]
    
    print("\n🤖 Testing AI explanation generation...")
    explanation = generator.generate_pick_explanation(test_prediction, test_factors)
    
    print("\n✅ AI Explanation Generated:")
    print("=" * 60)
    print(explanation)
    print("=" * 60)
    print("\n🎉 AI integration is working!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()


