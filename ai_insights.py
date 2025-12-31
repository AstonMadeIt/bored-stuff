#!/usr/bin/env python3
"""
AI-Powered Insights Generator
Uses Anthropic Claude to generate natural language explanations of predictions
"""

import os
import json
from typing import Dict, List, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  anthropic package not installed. Install with: pip install anthropic")

class AIInsightsGenerator:
    """Generate AI-powered insights for predictions"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"⚠️  Failed to initialize Anthropic client: {e}")
    
    def generate_pick_explanation(self, prediction: Dict, edge_factors: List[Dict], shap_explanation: Optional[Dict] = None) -> str:
        """
        Generate a natural language explanation of why this pick was made
        
        Args:
            prediction: Prediction dictionary
            edge_factors: List of edge factor dicts
            shap_explanation: Optional SHAP explanation dict
            
        Returns a 5-bullet explanation in casual, realistic dialogue
        """
        if not self.client:
            return self._fallback_explanation(edge_factors)
        
        # Extract key info
        away_team = prediction.get('away_team', 'Away Team')
        home_team = prediction.get('home_team', 'Home Team')
        predicted_winner = prediction.get('predicted_winner', '')
        predicted_spread = abs(float(prediction.get('predicted_spread', 0) or 0))
        confidence = float(prediction.get('confidence_score', 0) or 0)
        vegas_spread = prediction.get('vegas_spread')
        
        # Extract REAL recent game data from prediction (if available)
        # This prevents AI from hallucinating specific numbers
        away_recent_record = None
        home_recent_record = None
        away_streak = None
        home_streak = None
        
        # Try to get from trends if passed via edge_factors context
        # Edge factors might have trend data embedded
        for factor in edge_factors:
            text = factor.get('text', '')
            # Look for actual records in edge factors
            if 'L10' in text or 'last 10' in text.lower():
                # Extract record if present
                pass
        
        # Build context from edge factors (but be explicit about what we DON'T know)
        edge_summary = []
        for factor in edge_factors[:5]:  # Top 5 factors
            edge_summary.append(f"- {factor['text']}")
        
        # Add explicit instruction to NOT make up specific numbers
        data_warning = ""
        if not away_recent_record or not home_recent_record:
            data_warning = "\n\n⚠️ IMPORTANT: Do NOT invent specific win/loss records (e.g., 'won 7 of last 8') unless explicitly provided in the Key Factors above. If recent records aren't provided, use general language like 'recent form' or 'lately' without specific numbers."
        
        vegas_info = ""
        if vegas_spread:
            vegas_spread_val = abs(float(vegas_spread))
            model_spread = predicted_spread
            divergence = abs(model_spread - vegas_spread_val)
            vegas_info = f"\nVegas Line: {vegas_spread_val:.1f} pts\nModel Prediction: {model_spread:.1f} pts\nDivergence: {divergence:.1f} pts"
        
        # Add SHAP explanation if available
        shap_info = ""
        try:
            from shap_explainer import format_shap_for_ai
            if shap_explanation:
                shap_info = format_shap_for_ai(shap_explanation)
        except ImportError:
            pass
        
        prompt = f"""You're a sharp sports analyst explaining a betting pick to a friend. Keep it casual, realistic, and conversational - like you're texting them.

Game: {away_team} @ {home_team}
Predicted Winner: {predicted_winner} by {predicted_spread:.1f} pts
Confidence: {confidence*100:.0f}%
{vegas_info}

Key Factors:
{chr(10).join(edge_summary)}
{shap_info}

CRITICAL RULES - USE REAL DATA ONLY:
- Key Factors above contain REAL standings data scraped from ESPN
- Look for entries like "Team Record: X-Y, Last 10: A-B, Streak: W/L#"
- USE these exact numbers when present:
  * "Last 10: 7-3" means they won 7 of their last 10 games - USE THIS
  * "Streak: L2" means they're on a 2-game losing streak - USE THIS
  * "Record: 24-8" is their season record - USE THIS
- You can say things like:
  * "They're 7-3 in their last 10 games" (if Last 10: 7-3 is in Key Factors)
  * "They're on a 2-game losing streak" (if Streak: L2 is in Key Factors)
  * "They're 24-8 this season" (if Record: 24-8 is in Key Factors)
- DO NOT invent numbers that aren't in Key Factors
- If standings data isn't in Key Factors, use general language ("recent form", "lately")
- Combine real standings with SHAP insights for powerful analysis
- Example: "They're 7-3 in their last 10, but our model sees their offense struggling vs. strong defenses (SHAP: -2.3 pts)"

Generate a 5-bullet explanation that:
1. Sounds like a real person talking (not a robot)
2. Uses casual language ("This team is hot right now" not "The team demonstrates positive momentum")
3. Explains WHY this pick makes sense
4. Mentions the model's edge vs Vegas if significant
5. Ends with conviction level

Format as 5 bullet points, each 1-2 sentences max. Only use specific numbers if they're in the Key Factors above.

Example style (ONLY use numbers from Key Factors):
• "Milwaukee's been on fire lately - strong recent form and averaging high PPG."
• "Charlotte's defense has been leaky on the road - giving up points consistently away from home."
• "Our model sees a 2.1 point edge here vs Vegas, which is pretty significant for a close game." (This number comes from Key Factors)
• "The Bucks have been strong at home - home court advantage is real." (General language, no made-up records)
• "I'm pretty confident in this one - the numbers line up and the momentum favors Milwaukee."

Now generate for this game:"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Using Haiku for cost efficiency
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            explanation = response.content[0].text.strip()
            
            # Format as bullets if not already
            if not explanation.startswith('•'):
                lines = explanation.split('\n')
                formatted = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('•'):
                        if line.startswith('-') or line[0].isdigit():
                            formatted.append(f"• {line.lstrip('- ').lstrip('0123456789. ')}")
                        else:
                            formatted.append(f"• {line}")
                    elif line:
                        formatted.append(line)
                explanation = '\n'.join(formatted[:5])  # Max 5 bullets
            
            return explanation
            
        except Exception as e:
            print(f"⚠️  AI generation failed: {e}")
            return self._fallback_explanation(edge_factors)
    
    def _fallback_explanation(self, edge_factors: List[Dict]) -> str:
        """Fallback explanation if AI is unavailable"""
        if not edge_factors:
            return "• Model prediction based on recent team performance and matchup factors."
        
        bullets = []
        for factor in edge_factors[:5]:
            bullets.append(f"• {factor['text']}")
        
        return '\n'.join(bullets)
    
    def generate_game_summary(self, prediction: Dict, historical_data: Dict) -> str:
        """
        Generate a quick game preview/summary
        
        Returns a 2-3 sentence casual preview
        """
        if not self.client:
            return ""
        
        away_team = prediction.get('away_team', 'Away Team')
        home_team = prediction.get('home_team', 'Home Team')
        predicted_winner = prediction.get('predicted_winner', '')
        predicted_spread = abs(float(prediction.get('predicted_spread', 0) or 0))
        
        prompt = f"""Write a quick 2-3 sentence game preview in casual, engaging language.

Game: {away_team} @ {home_team}
Predicted Winner: {predicted_winner} by {predicted_spread:.1f} pts

Make it sound like a sports podcast host giving a quick preview. Be specific and engaging.

Example style:
"This should be a good one. Milwaukee's been rolling at home lately, but Charlotte's got some momentum coming off that big win. I like the Bucks here - they've been covering spreads consistently and the home court advantage is real."

Now write for this game:"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Using Haiku for cost efficiency
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"⚠️  AI summary generation failed: {e}")
            return ""

def generate_ai_explanation(prediction: Dict, edge_factors: List[Dict], api_key: Optional[str] = None) -> str:
    """Convenience function to generate AI explanation"""
    generator = AIInsightsGenerator(api_key=api_key)
    return generator.generate_pick_explanation(prediction, edge_factors)

