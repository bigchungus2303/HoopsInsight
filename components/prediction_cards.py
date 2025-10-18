"""
Prediction Cards Component

Displays next-game predictions with:
- Success probability percentages
- Visual progress bars
- Confidence indicators (High/Low)
- Color-coded confidence levels
"""

import streamlit as st


def show_prediction_card(stat_name, emoji, probability_results, stat_key):
    """
    Display prediction card for a single stat category.
    
    Args:
        stat_name: Display name of the stat (e.g., "Points")
        emoji: Emoji to display (e.g., "🏀")
        probability_results: Dictionary containing prediction data
        stat_key: Key for the stat in probability_results (e.g., "pts")
    """
    if stat_key in probability_results:
        st.subheader(f"{emoji} {stat_name}")
        for threshold, data in sorted(probability_results[stat_key].items()):
            success_prob = data['weighted_frequency']
            confidence = "High" if data['n_exceeds'] >= 5 else "Low"
            
            # Apply Bayesian smoothing if available
            if data.get('bayesian_smoothed'):
                bayes = data['bayesian_smoothed']
                success_prob = bayes['smoothed_probability']
            
            # Clean, simple metric display
            conf_emoji = "🟢" if confidence == "High" else "🟡"
            st.metric(
                f"≥ {threshold} {stat_name.lower()}",
                f"{success_prob*100:.1f}%",
                f"{conf_emoji} {confidence} confidence"
            )


def show_all_predictions(probability_results):
    """
    Display all prediction cards in a two-column layout.
    
    Args:
        probability_results: Dictionary containing all prediction data
    """
    col1, col2 = st.columns(2)
    
    with col1:
        # Points predictions
        show_prediction_card("Points", "🏀", probability_results, "pts")
        
        # Assists predictions
        show_prediction_card("Assists", "🎯", probability_results, "ast")
    
    with col2:
        # Rebounds predictions
        show_prediction_card("Rebounds", "💪", probability_results, "reb")
        
        # 3-Pointers predictions
        show_prediction_card("3-Pointers", "🎯", probability_results, "fg3m")

