"""
Charts Component

Reusable chart creation functions for:
- Recent game performance (multi-panel line charts)
- Probability analysis (grouped bar charts)
- Fatigue curves
- Minutes trend
- Player comparison charts
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def create_recent_games_chart(games_df, season_stats=None):
    """
    Create multi-panel chart showing recent game performance.
    
    Args:
        games_df: DataFrame with game data (date, pts, reb, ast, min)
        season_stats: Optional dict with season averages to show as horizontal lines
    
    Returns:
        Plotly figure object
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Points', 'Rebounds', 'Assists', 'Minutes Played'),
        vertical_spacing=0.12
    )
    
    fig.add_trace(go.Scatter(x=games_df['date'], y=games_df['pts'], 
                            mode='lines+markers', name='Points', line=dict(color='#1f77b4')),
                 row=1, col=1)
    fig.add_trace(go.Scatter(x=games_df['date'], y=games_df['reb'],
                            mode='lines+markers', name='Rebounds', line=dict(color='#ff7f0e')),
                 row=1, col=2)
    fig.add_trace(go.Scatter(x=games_df['date'], y=games_df['ast'],
                            mode='lines+markers', name='Assists', line=dict(color='#2ca02c')),
                 row=2, col=1)
    fig.add_trace(go.Scatter(x=games_df['date'], y=games_df['min'],
                            mode='lines+markers', name='Minutes', line=dict(color='#d62728')),
                 row=2, col=2)
    
    # Add season averages as horizontal lines if provided
    if season_stats:
        fig.add_hline(y=float(season_stats.get('pts', 0)), line_dash="dash", line_color="gray", row=1, col=1)
        fig.add_hline(y=float(season_stats.get('reb', 0)), line_dash="dash", line_color="gray", row=1, col=2)
        fig.add_hline(y=float(season_stats.get('ast', 0)), line_dash="dash", line_color="gray", row=2, col=1)
        # Parse minutes if in MM:SS format
        min_val = season_stats.get('min', 0)
        if isinstance(min_val, str) and ':' in min_val:
            parts = min_val.split(':')
            min_val = int(parts[0]) + int(parts[1]) / 60.0
        fig.add_hline(y=float(min_val), line_dash="dash", line_color="gray", row=2, col=2)
    
    fig.update_layout(height=500, showlegend=False, title_text="Last 10 Games (Dashed lines = Season Average)")
    return fig


def create_probability_bar_chart(probability_results, thresholds):
    """
    Create grouped bar chart for frequency vs inverse-likelihood.
    
    Args:
        probability_results: Dictionary with probability data
        thresholds: Dictionary with threshold values
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    stats_to_plot = ['pts', 'reb', 'ast', 'fg3m']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, stat in enumerate(stats_to_plot):
        if stat in probability_results:
            thresholds_list = list(probability_results[stat].keys())
            frequencies = [probability_results[stat][t]['frequency'] for t in thresholds_list]
            inverse_probs = [probability_results[stat][t]['inverse_probability'] for t in thresholds_list]
            
            x_pos = np.array(thresholds_list) + i * 0.8
            
            fig.add_trace(go.Bar(
                x=x_pos, y=frequencies,
                name=f'{stat.upper()} Frequency',
                marker_color=colors[i],
                opacity=0.7
            ))
            
            fig.add_trace(go.Bar(
                x=x_pos + 0.4, y=inverse_probs,
                name=f'{stat.upper()} Cool-off Prob',
                marker_color=colors[i],
                opacity=1.0,
                marker_pattern_shape="/"
            ))
    
    fig.update_layout(
        title="Frequency vs Cool-off Probability",
        xaxis_title="Threshold Values",
        yaxis_title="Probability",
        barmode='group',
        height=400
    )
    
    return fig


def create_fatigue_chart(games_df, window_size=10):
    """
    Create fatigue analysis chart with rolling average.
    
    Args:
        games_df: DataFrame with game data (pts)
        window_size: Window for rolling average
    
    Returns:
        Plotly figure object
    """
    rolling_avg = games_df['pts'].rolling(window=window_size, min_periods=5).mean()
    long_term_mean = games_df['pts'].mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=games_df.index, y=games_df['pts'], 
                           mode='markers', name='Game Points', opacity=0.6))
    fig.add_trace(go.Scatter(x=games_df.index, y=rolling_avg,
                           mode='lines', name='10-Game Rolling Average'))
    fig.add_hline(y=long_term_mean, line_dash="dash", 
                 annotation_text=f"Long-term Mean: {long_term_mean:.1f}")
    
    fig.update_layout(title="Points Fatigue Analysis", height=350)
    return fig


def create_minutes_trend_chart(games_df):
    """
    Create minutes played trend chart.
    
    Args:
        games_df: DataFrame with game data (min)
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=games_df.index, y=games_df['min'],
                           mode='lines+markers', name='Minutes Played'))
    
    fig.update_layout(title="Minutes Played Trend", height=350)
    return fig


def create_comparison_chart(player1_stats, player2_stats, player1_name, player2_name):
    """
    Create side-by-side comparison bar chart.
    
    Args:
        player1_stats: Dict with player 1 season stats
        player2_stats: Dict with player 2 season stats
        player1_name: Player 1 last name
        player2_name: Player 2 last name
    
    Returns:
        Plotly figure object
    """
    comparison_stats = ['pts', 'reb', 'ast', 'fg_pct', 'fg3_pct']
    
    fig = go.Figure(data=[
        go.Bar(name=player1_name, x=comparison_stats, 
               y=[player1_stats[stat] for stat in comparison_stats],
               marker_color='#1f77b4'),
        go.Bar(name=player2_name, x=comparison_stats,
               y=[player2_stats[stat] for stat in comparison_stats],
               marker_color='#ff7f0e')
    ])
    
    fig.update_layout(barmode='group', title="Season Averages Comparison",
                     xaxis_title="Statistics", yaxis_title="Values")
    return fig

