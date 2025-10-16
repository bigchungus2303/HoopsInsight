import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta

from nba_api import NBAAPIClient
from statistics import StatisticsEngine
from models import InverseFrequencyModel

# Initialize session state
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None
if 'player_data' not in st.session_state:
    st.session_state.player_data = None
if 'comparison_player' not in st.session_state:
    st.session_state.comparison_player = None
if 'comparison_data' not in st.session_state:
    st.session_state.comparison_data = None

# Initialize API client and engines
api_client = NBAAPIClient()
stats_engine = StatisticsEngine()
model = InverseFrequencyModel()

st.set_page_config(
    page_title="NBA Performance Predictor",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏀 NBA Player Performance Predictor")
st.markdown("*Regression-to-Mean Analysis with Inverse-Frequency Probability Modeling*")

# Sidebar for player search
with st.sidebar:
    st.header("Player Search")
    
    # Player search
    search_query = st.text_input("Search Player Name", placeholder="Enter player name...")
    
    if search_query and len(search_query) >= 2:
        with st.spinner("Searching players..."):
            players = api_client.search_players(search_query)
        
        if players:
            player_options = [f"{p['first_name']} {p['last_name']} ({p['team']['abbreviation']})" for p in players]
            selected_player_idx = st.selectbox("Select Player", range(len(player_options)), format_func=lambda x: player_options[x])
            
            if st.button("Load Player Data"):
                with st.spinner("Loading player data..."):
                    player = players[selected_player_idx]
                    st.session_state.selected_player = player
                    
                    # Fetch comprehensive player data
                    season_stats = api_client.get_season_stats(player['id'], 2024)
                    recent_games = api_client.get_recent_games(player['id'], limit=20)
                    career_stats = api_client.get_career_stats(player['id'])
                    
                    st.session_state.player_data = {
                        'player': player,
                        'season_stats': season_stats,
                        'recent_games': recent_games,
                        'career_stats': career_stats
                    }
    
    # Comparison player search
    st.header("Player Comparison")
    comparison_query = st.text_input("Search Comparison Player", placeholder="Enter second player name...")
    
    if comparison_query and len(comparison_query) >= 2:
        with st.spinner("Searching players..."):
            comparison_players = api_client.search_players(comparison_query)
        
        if comparison_players:
            comp_options = [f"{p['first_name']} {p['last_name']} ({p['team']['abbreviation']})" for p in comparison_players]
            selected_comp_idx = st.selectbox("Select Comparison Player", range(len(comp_options)), format_func=lambda x: comp_options[x])
            
            if st.button("Load Comparison Data"):
                with st.spinner("Loading comparison data..."):
                    comp_player = comparison_players[selected_comp_idx]
                    st.session_state.comparison_player = comp_player
                    
                    comp_season_stats = api_client.get_season_stats(comp_player['id'], 2024)
                    comp_recent_games = api_client.get_recent_games(comp_player['id'], limit=20)
                    comp_career_stats = api_client.get_career_stats(comp_player['id'])
                    
                    st.session_state.comparison_data = {
                        'player': comp_player,
                        'season_stats': comp_season_stats,
                        'recent_games': comp_recent_games,
                        'career_stats': comp_career_stats
                    }

# Main content area
if st.session_state.player_data is None:
    st.info("👈 Search and select a player from the sidebar to begin analysis")
    st.markdown("""
    ### Features:
    - **Player Search**: Find NBA players with autocomplete
    - **Season Statistics**: View per-game averages with z-score normalization
    - **Recent Performance**: Analyze last 20 games with trend visualization
    - **Inverse-Frequency Model**: Calculate regression-to-mean probabilities
    - **Career Phase Weighting**: Adjust for early/peak/late career phases
    - **Player Comparison**: Side-by-side statistical analysis
    - **Fatigue Analysis**: Detect performance sustainability patterns
    """)
else:
    player_info = st.session_state.player_data
    player = player_info['player']
    season_stats = player_info['season_stats']
    recent_games = player_info['recent_games']
    
    # Player info header
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader(f"{player['first_name']} {player['last_name']}")
        st.write(f"**Team**: {player['team']['full_name']}")
        st.write(f"**Position**: {player['position'] if player['position'] else 'N/A'}")
    
    with col2:
        if player.get('height_feet') and player.get('height_inches'):
            height = f"{player['height_feet']}'{player['height_inches']}\""
        else:
            height = "N/A"
        st.write(f"**Height**: {height}")
        st.write(f"**Weight**: {player['weight_pounds']} lbs" if player['weight_pounds'] else "Weight: N/A")
    
    with col3:
        if st.button("Clear Selection"):
            st.session_state.selected_player = None
            st.session_state.player_data = None
            st.rerun()
    
    st.divider()
    
    # Season Statistics with Z-Score Normalization
    st.header("📊 Season Statistics (2024)")
    
    if season_stats:
        # Calculate league averages for z-score normalization
        league_averages = stats_engine.get_league_averages(2024)
        
        stats_df = pd.DataFrame([season_stats])
        normalized_stats = stats_engine.calculate_z_scores(stats_df, league_averages)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Points per Game", f"{season_stats['pts']:.1f}", 
                     f"Z-Score: {normalized_stats['pts_z'][0]:.2f}")
            st.metric("Field Goal %", f"{season_stats['fg_pct']:.3f}", 
                     f"Z-Score: {normalized_stats['fg_pct_z'][0]:.2f}")
        
        with col2:
            st.metric("Rebounds per Game", f"{season_stats['reb']:.1f}",
                     f"Z-Score: {normalized_stats['reb_z'][0]:.2f}")
            st.metric("3-Point %", f"{season_stats['fg3_pct']:.3f}",
                     f"Z-Score: {normalized_stats['fg3_pct_z'][0]:.2f}")
        
        with col3:
            st.metric("Assists per Game", f"{season_stats['ast']:.1f}",
                     f"Z-Score: {normalized_stats['ast_z'][0]:.2f}")
            st.metric("Free Throw %", f"{season_stats['ft_pct']:.3f}",
                     f"Z-Score: {normalized_stats['ft_pct_z'][0]:.2f}")
        
        with col4:
            st.metric("Minutes per Game", f"{season_stats['min']:.1f}",
                     f"Z-Score: {normalized_stats['min_z'][0]:.2f}")
            st.metric("Games Played", f"{season_stats['games_played']}")
    
    # Recent Game Performance
    st.header("📈 Recent Game Performance")
    
    if recent_games and len(recent_games) > 0:
        games_df = pd.DataFrame(recent_games)
        games_df['date'] = pd.to_datetime(games_df['date'])
        games_df = games_df.sort_values('date').tail(10)  # Last 10 games
        
        # Create line chart for recent performance
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
        
        # Add season averages as horizontal lines
        if season_stats:
            fig.add_hline(y=season_stats['pts'], line_dash="dash", line_color="gray", row=1, col=1)
            fig.add_hline(y=season_stats['reb'], line_dash="dash", line_color="gray", row=1, col=2)
            fig.add_hline(y=season_stats['ast'], line_dash="dash", line_color="gray", row=2, col=1)
            fig.add_hline(y=season_stats['min'], line_dash="dash", line_color="gray", row=2, col=2)
        
        fig.update_layout(height=500, showlegend=False, title_text="Last 10 Games (Dashed lines = Season Average)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent games table
        display_games = games_df[['date', 'pts', 'reb', 'ast', 'fg_pct', 'fg3m', 'min']].copy()
        display_games['date'] = display_games['date'].dt.strftime('%m/%d')
        display_games.columns = ['Date', 'PTS', 'REB', 'AST', 'FG%', '3PM', 'MIN']
        st.dataframe(display_games, use_container_width=True)
    
    # Inverse-Frequency Probability Analysis
    st.header("🎯 Regression-to-Mean Analysis")
    
    if recent_games and season_stats:
        # Define thresholds for analysis
        thresholds = {
            'pts': [10, 15, 20, 25, 30],
            'reb': [4, 6, 8, 10, 12],
            'ast': [4, 6, 8, 10, 12],
            'fg3m': [2, 3, 5, 7]
        }
        
        # Calculate dynamic thresholds based on player's season stats
        dynamic_thresholds = stats_engine.calculate_dynamic_thresholds(season_stats)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Fixed Thresholds Analysis")
            
            games_df = pd.DataFrame(recent_games)
            probability_results = model.calculate_inverse_frequency_probabilities(
                games_df, thresholds, alpha=0.85
            )
            
            # Create grouped bar chart
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
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Dynamic Thresholds (Player-Specific)")
            
            # Show dynamic thresholds table
            dynamic_df = pd.DataFrame([
                {'Stat': 'Points', 'Mean': f"{dynamic_thresholds['pts']['mean']:.1f}",
                 'μ+σ': f"{dynamic_thresholds['pts']['plus_1_std']:.1f}",
                 'μ+2σ': f"{dynamic_thresholds['pts']['plus_2_std']:.1f}",
                 'μ+3σ': f"{dynamic_thresholds['pts']['plus_3_std']:.1f}"},
                {'Stat': 'Rebounds', 'Mean': f"{dynamic_thresholds['reb']['mean']:.1f}",
                 'μ+σ': f"{dynamic_thresholds['reb']['plus_1_std']:.1f}",
                 'μ+2σ': f"{dynamic_thresholds['reb']['plus_2_std']:.1f}",
                 'μ+3σ': f"{dynamic_thresholds['reb']['plus_3_std']:.1f}"},
                {'Stat': 'Assists', 'Mean': f"{dynamic_thresholds['ast']['mean']:.1f}",
                 'μ+σ': f"{dynamic_thresholds['ast']['plus_1_std']:.1f}",
                 'μ+2σ': f"{dynamic_thresholds['ast']['plus_2_std']:.1f}",
                 'μ+3σ': f"{dynamic_thresholds['ast']['plus_3_std']:.1f}"}
            ])
            
            st.dataframe(dynamic_df, use_container_width=True)
            
            # Calculate probabilities for dynamic thresholds
            dynamic_prob_results = model.calculate_dynamic_threshold_probabilities(
                games_df, dynamic_thresholds, alpha=0.85
            )
            
            st.write("**Cool-off Probabilities at Dynamic Thresholds:**")
            for stat in ['pts', 'reb', 'ast']:
                if stat in dynamic_prob_results:
                    st.write(f"**{stat.upper()}:**")
                    for threshold, data in dynamic_prob_results[stat].items():
                        st.write(f"  - {threshold}: {data['inverse_probability']:.3f}")
    
    # Career Phase and Fatigue Analysis
    st.header("⚡ Career Phase & Fatigue Analysis")
    
    if recent_games and len(recent_games) >= 10:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Fatigue/Load Curve")
            
            games_df = pd.DataFrame(recent_games)
            games_df = games_df.sort_values('date')
            
            # Calculate rolling averages
            rolling_10 = games_df['pts'].rolling(window=10, min_periods=5).mean()
            long_term_mean = games_df['pts'].mean()
            
            fatigue_analysis = model.analyze_fatigue_curve(games_df, window_size=10)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=games_df.index, y=games_df['pts'], 
                                   mode='markers', name='Game Points', opacity=0.6))
            fig.add_trace(go.Scatter(x=games_df.index, y=rolling_10,
                                   mode='lines', name='10-Game Rolling Average'))
            fig.add_hline(y=long_term_mean, line_dash="dash", 
                         annotation_text=f"Long-term Mean: {long_term_mean:.1f}")
            
            if fatigue_analysis['regression_risk'] > 0.5:
                fig.add_annotation(x=len(games_df)-1, y=games_df['pts'].iloc[-1],
                                 text=f"High Regression Risk: {fatigue_analysis['regression_risk']:.2f}",
                                 showarrow=True, arrowcolor="red")
            
            fig.update_layout(title="Points Fatigue Analysis", height=350)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Minutes Trend Filter")
            
            # Analyze minutes played trend
            minutes_trend = model.analyze_minutes_trend(games_df)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=games_df.index, y=games_df['min'],
                                   mode='lines+markers', name='Minutes Played'))
            
            if minutes_trend['declining_trend']:
                fig.add_annotation(text="Declining Minutes Detected", 
                                 x=0.5, y=0.9, xref="paper", yref="paper",
                                 showarrow=False, bgcolor="yellow")
            
            fig.update_layout(title="Minutes Played Trend", height=350)
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("Minutes Trend", "Declining" if minutes_trend['declining_trend'] else "Stable",
                     f"Slope: {minutes_trend['trend_slope']:.2f}")
            st.metric("Sustainability Factor", f"{minutes_trend['sustainability_factor']:.3f}")

# Player Comparison Section
if st.session_state.comparison_data and st.session_state.player_data:
    st.header("⚖️ Player Comparison")
    
    player1_data = st.session_state.player_data
    player2_data = st.session_state.comparison_data
    
    player1 = player1_data['player']
    player2 = player2_data['player']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"{player1['first_name']} {player1['last_name']}")
        if player1_data['season_stats']:
            stats1 = player1_data['season_stats']
            st.metric("PPG", f"{stats1['pts']:.1f}")
            st.metric("RPG", f"{stats1['reb']:.1f}")
            st.metric("APG", f"{stats1['ast']:.1f}")
            st.metric("FG%", f"{stats1['fg_pct']:.3f}")
    
    with col2:
        st.subheader(f"{player2['first_name']} {player2['last_name']}")
        if player2_data['season_stats']:
            stats2 = player2_data['season_stats']
            st.metric("PPG", f"{stats2['pts']:.1f}")
            st.metric("RPG", f"{stats2['reb']:.1f}")
            st.metric("APG", f"{stats2['ast']:.1f}")
            st.metric("FG%", f"{stats2['fg_pct']:.3f}")
    
    # Comparative bar chart
    if player1_data['season_stats'] and player2_data['season_stats']:
        comparison_stats = ['pts', 'reb', 'ast', 'fg_pct', 'fg3_pct']
        
        fig = go.Figure(data=[
            go.Bar(name=f"{player1['last_name']}", x=comparison_stats, 
                   y=[player1_data['season_stats'][stat] for stat in comparison_stats],
                   marker_color='#1f77b4'),
            go.Bar(name=f"{player2['last_name']}", x=comparison_stats,
                   y=[player2_data['season_stats'][stat] for stat in comparison_stats],
                   marker_color='#ff7f0e')
        ])
        
        fig.update_layout(barmode='group', title="Season Averages Comparison",
                         xaxis_title="Statistics", yaxis_title="Values")
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.markdown("**Data Source**: [balldontlie.io](https://balldontlie.io) | **Model**: Inverse-Frequency Probability with Career Phase Weighting")
