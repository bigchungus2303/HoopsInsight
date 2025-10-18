"""
Simplified, user-friendly prediction cards for NBA player performance
Replaces technical jargon with actionable insights and betting recommendations
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any

def get_performance_indicator(regression_prob: float, recent_frequency: float, threshold: float) -> tuple:
    """
    Determine performance indicator and betting recommendation
    
    Returns:
        (indicator_emoji, indicator_text, bet_recommendation, risk_level)
    """
    # Performance indicators
    if regression_prob >= 0.75:
        indicator_emoji = "❄️"
        indicator_text = "COLD"
        bet_rec = "UNDER"
        risk_level = "HIGH" if regression_prob >= 0.85 else "MEDIUM"
    elif regression_prob <= 0.35:
        indicator_emoji = "🔥"
        indicator_text = "HOT"
        bet_rec = "OVER"
        risk_level = "HIGH" if regression_prob <= 0.25 else "MEDIUM"
    elif 0.45 <= regression_prob <= 0.65:
        indicator_emoji = "📊"
        indicator_text = "STEADY"
        bet_rec = "NEUTRAL"
        risk_level = "LOW"
    else:
        indicator_emoji = "⚡"
        indicator_text = "VOLATILE"
        bet_rec = "AVOID"
        risk_level = "HIGH"
    
    return indicator_emoji, indicator_text, bet_rec, risk_level

def get_confidence_level(confidence: str) -> tuple:
    """Convert confidence to user-friendly terms"""
    confidence_map = {
        "High": ("✅", "HIGH"),
        "Medium": ("⚠️", "MEDIUM"), 
        "Low": ("❌", "LOW")
    }
    return confidence_map.get(confidence, ("❓", "UNKNOWN"))

def get_insight_message(regression_prob: float, recent_frequency: float, stat: str, threshold: float) -> str:
    """Generate actionable insight message"""
    if regression_prob >= 0.8:
        if recent_frequency <= 0.2:
            return f"Player struggling with {stat.lower()} - expect continued low performance"
        else:
            return f"Recent hot streak ending - {stat.lower()} likely to cool off"
    elif regression_prob <= 0.3:
        if recent_frequency >= 0.7:
            return f"Consistent high performer - {stat.lower()} streak likely to continue"
        else:
            return f"Player heating up - {stat.lower()} trending upward"
    elif 0.4 <= regression_prob <= 0.6:
        return f"Steady performer - {stat.lower()} around average level"
    else:
        return f"Unpredictable {stat.lower()} - high variance in recent games"

def create_simple_prediction_card(stat: str, threshold: float, data: Dict[str, Any]) -> None:
    """
    Create a user-friendly prediction card
    
    Args:
        stat: Statistics name (pts, reb, ast, etc.)
        threshold: Threshold value
        data: Prediction data dictionary
    """
    # Extract data
    regression_prob = data.get('weighted_inverse_probability', 0.5)
    confidence = data.get('confidence', 'Medium')
    recent_frequency = data.get('recent_frequency', 0.5)
    recent_games = data.get('recent_games', 10)
    
    # Get indicators
    indicator_emoji, indicator_text, bet_rec, risk_level = get_performance_indicator(
        regression_prob, recent_frequency, threshold
    )
    conf_emoji, conf_text = get_confidence_level(confidence)
    
    # Generate insight
    insight = get_insight_message(regression_prob, recent_frequency, stat, threshold)
    
    # Format threshold display
    stat_display = {
        'pts': 'Points',
        'reb': 'Rebounds', 
        'ast': 'Assists',
        'fg3m': '3-Pointers Made',
        'fg3a': '3-Pointers Attempted',
        'fgm': 'Field Goals Made',
        'fga': 'Field Goals Attempted',
        'ftm': 'Free Throws Made',
        'fta': 'Free Throws Attempted',
        'stl': 'Steals',
        'blk': 'Blocks',
        'tov': 'Turnovers',
        'pf': 'Personal Fouls'
    }.get(stat, stat.upper())
    
    # Create card
    with st.container():
        st.markdown(f"### 🎯 {stat_display} ≥ {int(threshold)}")
        
        # Main prediction row
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if regression_prob >= 0.65:
                st.markdown(f"**❌ UNLIKELY**")
            else:
                st.markdown(f"**✅ LIKELY**")
        
        with col2:
            st.markdown(f"{indicator_emoji} **{indicator_text}**")
        
        with col3:
            if bet_rec == "OVER":
                st.markdown(f"💡 **BET: {bet_rec}**")
            elif bet_rec == "UNDER":
                st.markdown(f"💡 **BET: {bet_rec}**")
            elif bet_rec == "NEUTRAL":
                st.markdown(f"💡 **{bet_rec}**")
            else:
                st.markdown(f"💡 **{bet_rec}**")
        
        # Details row removed - keeping it simple
        
        # Insight message
        st.info(f"💡 {insight}")
        
        st.divider()

def show_simple_predictions(probability_results: Dict[str, Dict]) -> None:
    """
    Display all predictions using simplified, user-friendly cards
    
    Args:
        probability_results: Dictionary of prediction results from the model
    """
    if not probability_results:
        st.warning("⚠️ No prediction data available")
        return
    
    st.subheader("🎯 Next Game Predictions")
    st.caption("Simple, actionable insights for betting and fantasy decisions")
    
    # Group predictions by stat
    for stat, thresholds in probability_results.items():
        if not thresholds:
            continue
            
        st.markdown(f"#### {stat.upper()} Predictions")
        
        # Sort thresholds for better display
        sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[0])
        
        for threshold, data in sorted_thresholds:
            create_simple_prediction_card(stat, threshold, data)
        
        st.markdown("---")

def show_betting_summary(probability_results: Dict[str, Dict]) -> None:
    """
    Show a quick betting summary with top recommendations
    """
    if not probability_results:
        return
    
    st.subheader("🎰 Quick Betting Guide")
    
    recommendations = []
    
    for stat, thresholds in probability_results.items():
        for threshold, data in probability_results[stat].items():
            regression_prob = data.get('weighted_inverse_probability', 0.5)
            confidence = data.get('confidence', 'Medium')
            
            if regression_prob >= 0.75:  # Strong UNDER bet
                recommendations.append({
                    'type': 'UNDER',
                    'stat': stat,
                    'threshold': threshold,
                    'confidence': regression_prob,
                    'strength': 'STRONG' if regression_prob >= 0.85 else 'MODERATE'
                })
            elif regression_prob <= 0.35:  # Strong OVER bet
                recommendations.append({
                    'type': 'OVER', 
                    'stat': stat,
                    'threshold': threshold,
                    'confidence': 1 - regression_prob,
                    'strength': 'STRONG' if regression_prob <= 0.25 else 'MODERATE'
                })
    
    if recommendations:
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔥 Best OVER Bets:**")
            over_bets = [r for r in recommendations if r['type'] == 'OVER'][:3]
            for bet in over_bets:
                st.markdown(f"• {bet['stat'].upper()} ≥ {int(bet['threshold'])} ({bet['strength']})")
        
        with col2:
            st.markdown("**❄️ Best UNDER Bets:**")
            under_bets = [r for r in recommendations if r['type'] == 'UNDER'][:3]
            for bet in under_bets:
                st.markdown(f"• {bet['stat'].upper()} ≥ {int(bet['threshold'])} ({bet['strength']})")
    else:
        st.info("💡 No strong betting recommendations at current thresholds")
