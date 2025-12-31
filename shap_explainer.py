#!/usr/bin/env python3
"""
SHAP Explainer for Individual Predictions
Computes SHAP values for real-time prediction explanations
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️  SHAP not available. Install with: pip install shap")

class SHAPExplainer:
    """Generate SHAP explanations for individual predictions"""
    
    def __init__(self, model, features: List[str], background_data: Optional[pd.DataFrame] = None):
        """
        Initialize SHAP explainer
        
        Args:
            model: Trained model (CatBoost, XGBoost, or LightGBM)
            features: List of feature names
            background_data: Background dataset for SHAP (optional, uses model's expected_value if None)
        """
        self.model = model
        self.features = features
        self.explainer = None
        self.background_data = background_data
        
        if SHAP_AVAILABLE:
            try:
                # Use TreeExplainer for tree-based models
                self.explainer = shap.TreeExplainer(model, background_data)
            except Exception as e:
                print(f"⚠️  SHAP TreeExplainer failed: {e}")
                try:
                    # Fallback to KernelExplainer
                    if background_data is not None:
                        self.explainer = shap.KernelExplainer(model.predict, background_data)
                except Exception as e2:
                    print(f"⚠️  SHAP KernelExplainer also failed: {e2}")
    
    def explain_prediction(self, X: pd.DataFrame) -> Optional[Dict]:
        """
        Generate SHAP explanation for a single prediction
        
        Args:
            X: DataFrame with features for one prediction
            
        Returns:
            Dict with:
                - shap_values: Array of SHAP values
                - feature_importance: Dict mapping feature names to importance scores
                - top_features: List of top contributing features
        """
        if not self.explainer or X.empty:
            return None
        
        try:
            # Compute SHAP values
            shap_values = self.explainer.shap_values(X)
            
            # Handle different return types
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # For multi-output models
            
            # Convert to array if needed
            if hasattr(shap_values, 'values'):
                shap_values = shap_values.values
            
            shap_values = np.array(shap_values).flatten()
            
            # Get feature importance (absolute SHAP values)
            feature_importance = {}
            top_features = []
            
            for i, feature_name in enumerate(self.features):
                if i < len(shap_values):
                    importance = abs(float(shap_values[i]))
                    feature_importance[feature_name] = {
                        'shap_value': float(shap_values[i]),
                        'importance': importance
                    }
            
            # Sort by importance
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1]['importance'],
                reverse=True
            )
            
            # Get top 10 features
            top_features = [
                {
                    'feature': name,
                    'shap_value': info['shap_value'],
                    'importance': info['importance'],
                    'direction': 'increases' if info['shap_value'] > 0 else 'decreases'
                }
                for name, info in sorted_features[:10]
            ]
            
            return {
                'shap_values': shap_values.tolist(),
                'feature_importance': feature_importance,
                'top_features': top_features,
                'base_value': float(self.explainer.expected_value) if hasattr(self.explainer, 'expected_value') else None
            }
            
        except Exception as e:
            print(f"⚠️  SHAP explanation failed: {e}")
            return None
    
    @staticmethod
    def load_explainer_from_training(model, features: List[str], shap_file: str = 'models/shap_values.pkl') -> Optional['SHAPExplainer']:
        """
        Load SHAP explainer using background data from training
        
        Args:
            model: Trained model
            features: List of feature names
            shap_file: Path to saved SHAP values from training
            
        Returns:
            SHAPExplainer instance or None
        """
        try:
            with open(shap_file, 'rb') as f:
                shap_data = pickle.load(f)
            
            # Use X_test as background data
            background_data = shap_data.get('X_test')
            
            if background_data is not None:
                # Convert to DataFrame if needed
                if isinstance(background_data, np.ndarray):
                    background_data = pd.DataFrame(background_data, columns=features)
                
                # Sample background data (SHAP can be slow with large datasets)
                if len(background_data) > 100:
                    background_data = background_data.sample(100, random_state=42)
                
                return SHAPExplainer(model, features, background_data)
            else:
                return SHAPExplainer(model, features)
                
        except FileNotFoundError:
            print(f"⚠️  SHAP file not found: {shap_file}")
            return SHAPExplainer(model, features)
        except Exception as e:
            print(f"⚠️  Failed to load SHAP explainer: {e}")
            return SHAPExplainer(model, features)

def get_shap_explanation_for_prediction(
    model,
    X: pd.DataFrame,
    features: List[str],
    shap_file: Optional[str] = None
) -> Optional[Dict]:
    """
    Convenience function to get SHAP explanation for a prediction
    
    Args:
        model: Trained model
        X: Feature DataFrame for one prediction
        features: List of feature names
        shap_file: Optional path to saved SHAP values
        
    Returns:
        SHAP explanation dict or None
    """
    if not SHAP_AVAILABLE:
        return None
    
    if shap_file and Path(shap_file).exists():
        explainer = SHAPExplainer.load_explainer_from_training(model, features, shap_file)
    else:
        explainer = SHAPExplainer(model, features)
    
    if explainer:
        return explainer.explain_prediction(X)
    
    return None

def format_shap_for_ai(shap_explanation: Dict) -> str:
    """
    Format SHAP explanation for AI prompt
    
    Args:
        shap_explanation: SHAP explanation dict
        
    Returns:
        Formatted string for AI prompt
    """
    if not shap_explanation or 'top_features' not in shap_explanation:
        return ""
    
    top_features = shap_explanation['top_features'][:5]  # Top 5
    
    formatted = "\nSHAP Feature Importance (What the model is actually using):\n"
    for i, feat in enumerate(top_features, 1):
        feature_name = feat['feature'].replace('_', ' ').title()
        direction = feat['direction']
        importance = feat['importance']
        
        # Make feature names more readable
        readable_name = feature_name
        if 'L5' in feature_name or 'L10' in feature_name:
            readable_name = feature_name.replace('L5', 'Last 5 Games').replace('L10', 'Last 10 Games')
        if 'Avg Points' in feature_name:
            readable_name = feature_name.replace('Avg Points', 'Scoring Average')
        if 'Rest' in feature_name:
            readable_name = feature_name.replace('Rest', 'Rest Days')
        
        formatted += f"{i}. {readable_name}: {direction} prediction by {importance:.2f} points\n"
    
    return formatted


