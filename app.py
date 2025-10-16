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
from export_utils import (export_player_stats_csv, export_player_stats_json,
                          export_probability_analysis_csv, export_comparison_csv,
                          export_comparison_json)
from database import NBADatabase

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
db = NBADatabase()

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
    
    # Favorites quick access
    favorites = db.get_favorites()
    if favorites:
        with st.expander("⭐ Favorites"):
            fav_season_years = list(range(2025, 2019, -1))
            fav_season_display = {year: f"{year}-{year+1}" for year in fav_season_years}
            
            fav_season_selected = st.selectbox(
                "Season for Favorites", 
                options=[fav_season_display[year] for year in fav_season_years],
                index=0,
                key="fav_season_selector"
            )
            # Extract the base year from display format
            fav_season = int(fav_season_selected.split('-')[0])
            for fav in favorites:
                if st.button(f"{fav['player_name']} ({fav['team_abbreviation']})", key=f"fav_{fav['player_id']}"):
                    # Load favorite player
                    player = api_client.get_player_info(fav['player_id'])
                    if player:
                        st.session_state.selected_player = player
                        st.session_state.selected_season = fav_season
                        
                        season_stats = api_client.get_season_stats(player['id'], fav_season)
                        recent_games = api_client.get_recent_games(player['id'], limit=20, season=fav_season)
                        career_stats = api_client.get_career_stats(player['id'])
                        
                        st.session_state.player_data = {
                            'player': player,
                            'season_stats': season_stats,
                            'recent_games': recent_games,
                            'career_stats': career_stats
                        }
                        st.rerun()
    
    # Player search with autocomplete
    search_query = st.text_input("Search Player Name", placeholder="Type player name (e.g., LeBron)...", key="player_search")
    
    # Season selection (display as "2024-2025" format)
    current_year = datetime.now().year
    season_year = current_year if datetime.now().month >= 10 else current_year - 1
    season_years = list(range(2025, 2019, -1))
    season_display = {year: f"{year}-{year+1}" for year in season_years}
    
    selected_season_display = st.selectbox(
        "Select Season", 
        options=[season_display[year] for year in season_years],
        index=0,
        key="season_selector"
    )
    # Extract the base year from the display format (e.g., "2024-2025" -> 2024)
    selected_season = int(selected_season_display.split('-')[0])
    
    # Initialize search results storage
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    
    # Autocomplete: Search automatically as user types
    if search_query and len(search_query) >= 2:
        players = api_client.search_players(search_query)
        
        if players:
            # Store players for selection
            st.session_state.search_results = players
            
            # Create autocomplete dropdown with player suggestions
            player_options = {f"{p['first_name']} {p['last_name']} ({p['team']['abbreviation']})": p for p in players}
            player_names = list(player_options.keys())
            
            selected_player_name = st.selectbox(
                "Select Player", 
                options=player_names,
                key="player_selector"
            )
            
            # Auto-load button - loads when user clicks
            if st.button("Load Player Data"):
                with st.spinner("Loading player data..."):
                    player = player_options[selected_player_name]
                    st.session_state.selected_player = player
                    st.session_state.selected_season = selected_season
                    
                    # Fetch comprehensive player data for selected season
                    season_stats = api_client.get_season_stats(player['id'], selected_season)
                    recent_games = api_client.get_recent_games(player['id'], limit=20, season=selected_season)
                    career_stats = api_client.get_career_stats(player['id'])
                    
                    st.session_state.player_data = {
                        'player': player,
                        'season_stats': season_stats,
                        'recent_games': recent_games,
                        'career_stats': career_stats
                    }
                    st.rerun()
        else:
            st.info("No players found. Try a different search term.")
    elif search_query and len(search_query) < 2:
        st.caption("Type at least 2 characters to search")
    
    st.divider()
    
    # Advanced Settings
    with st.expander("⚙️ Advanced Settings"):
        st.subheader("Custom Thresholds")
        
        # Points thresholds
        pts_thresholds_input = st.text_input(
            "Points Thresholds (comma-separated)", 
            value="10,15,20",
            key="pts_thresholds"
        )
        
        # Rebounds thresholds
        reb_thresholds_input = st.text_input(
            "Rebounds Thresholds (comma-separated)", 
            value="4,6,8,10",
            key="reb_thresholds"
        )
        
        # Assists thresholds
        ast_thresholds_input = st.text_input(
            "Assists Thresholds (comma-separated)", 
            value="4,6,8,10",
            key="ast_thresholds"
        )
        
        # 3-pointers thresholds
        fg3m_thresholds_input = st.text_input(
            "3-Pointers Thresholds (comma-separated)", 
            value="2,3,5",
            key="fg3m_thresholds"
        )
        
        # Alpha (recency weight)
        alpha_value = st.slider(
            "Recency Weight (α)", 
            min_value=0.5, 
            max_value=1.0, 
            value=0.85, 
            step=0.05,
            help="Higher values give more weight to recent games"
        )
        
        st.divider()
        st.subheader("Career Phase Decay Parameters")
        
        use_career_phase = st.checkbox(
            "Enable Career Phase Decay",
            value=False,
            help="Apply career phase weighting to predictions (early/peak/late career adjustments)"
        )
        
        lambda_early = st.slider(
            "λ Early Career",
            min_value=0.01,
            max_value=0.10,
            value=0.02,
            step=0.01,
            help="Lower decay = more weight on recent games for rising players",
            disabled=not use_career_phase
        )
        
        lambda_peak = st.slider(
            "λ Peak Career",
            min_value=0.01,
            max_value=0.15,
            value=0.05,
            step=0.01,
            help="Balanced weighting for stable performers",
            disabled=not use_career_phase
        )
        
        lambda_late = st.slider(
            "λ Late Career",
            min_value=0.01,
            max_value=0.20,
            value=0.08,
            step=0.01,
            help="Higher decay = stronger regression tendency for declining players",
            disabled=not use_career_phase
        )
        
        st.session_state.custom_thresholds = {
            'pts': [int(x.strip()) for x in pts_thresholds_input.split(',') if x.strip().isdigit()],
            'reb': [int(x.strip()) for x in reb_thresholds_input.split(',') if x.strip().isdigit()],
            'ast': [int(x.strip()) for x in ast_thresholds_input.split(',') if x.strip().isdigit()],
            'fg3m': [int(x.strip()) for x in fg3m_thresholds_input.split(',') if x.strip().isdigit()]
        }
        st.session_state.alpha = alpha_value
        st.session_state.use_career_phase = use_career_phase
        st.session_state.lambda_params = {
            'early': lambda_early,
            'peak': lambda_peak,
            'late': lambda_late
        }
    
    st.divider()
    
    # Comparison player search
    st.header("Player Comparison")
    comparison_query = st.text_input("Search Comparison Player", placeholder="Enter second player name...")
    
    comp_season_years = list(range(2025, 2019, -1))
    comp_season_display = {year: f"{year}-{year+1}" for year in comp_season_years}
    
    comp_season_selected = st.selectbox(
        "Comparison Season", 
        options=[comp_season_display[year] for year in comp_season_years],
        index=0,
        key="comp_season_selector"
    )
    # Extract the base year from display format
    comp_season = int(comp_season_selected.split('-')[0])
    
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
                    st.session_state.comparison_season = comp_season
                    
                    comp_season_stats = api_client.get_season_stats(comp_player['id'], comp_season)
                    comp_recent_games = api_client.get_recent_games(comp_player['id'], limit=20, season=comp_season)
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
        weight = player.get('weight_pounds')
        st.write(f"**Weight**: {weight} lbs" if weight else "**Weight**: N/A")
    
    with col3:
        # Favorites and export buttons
        col_a, col_b = st.columns(2)
        
        with col_a:
            is_favorite = db.is_favorite(player['id'])
            if is_favorite:
                if st.button("❤️ Remove Favorite"):
                    db.remove_favorite(player['id'])
                    st.rerun()
            else:
                if st.button("🤍 Add Favorite"):
                    db.add_favorite(player['id'], f"{player['first_name']} {player['last_name']}")
                    st.rerun()
        
        with col_b:
            if st.button("Clear Selection"):
                st.session_state.selected_player = None
                st.session_state.player_data = None
                st.rerun()
    
    st.divider()
    
    # Season Statistics with Z-Score Normalization
    display_season = st.session_state.get('selected_season', 2024)
    display_season_formatted = f"{display_season}-{display_season+1}"
    
    col_header, col_export = st.columns([3, 1])
    with col_header:
        st.header(f"📊 Season Statistics ({display_season_formatted})")
    with col_export:
        # Export buttons
        export_format = st.selectbox("Export", ["CSV", "JSON"], key="export_format_main")
        if st.button("📥 Export Data", key="export_main"):
            if export_format == "CSV":
                csv_data = export_player_stats_csv(player, season_stats, recent_games)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"{player['last_name']}_{display_season}_stats.csv",
                    mime="text/csv"
                )
            else:
                json_data = export_player_stats_json(player, season_stats, recent_games)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"{player['last_name']}_{display_season}_stats.json",
                    mime="application/json"
                )
    
    if season_stats:
        # Calculate league averages for z-score normalization
        league_averages = stats_engine.get_league_averages(display_season)
        
        stats_df = pd.DataFrame([season_stats])
        normalized_stats = stats_engine.calculate_z_scores(stats_df, league_averages)
        
        # Helper function to safely convert to float
        def safe_float(value, default=0.0):
            try:
                return float(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        # Helper function to convert MM:SS format to decimal minutes
        def parse_minutes(min_str):
            if not min_str:
                return 0.0
            try:
                # If already a number, return it
                return float(min_str)
            except (ValueError, TypeError):
                pass
            try:
                # Parse MM:SS format
                if isinstance(min_str, str) and ':' in min_str:
                    parts = min_str.split(':')
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    return minutes + (seconds / 60.0)
                return 0.0
            except:
                return 0.0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Points per Game", f"{safe_float(season_stats['pts']):.1f}", 
                     f"Z-Score: {normalized_stats['pts_z'][0]:.2f}")
            st.metric("Field Goal %", f"{safe_float(season_stats['fg_pct']):.3f}", 
                     f"Z-Score: {normalized_stats['fg_pct_z'][0]:.2f}")
        
        with col2:
            st.metric("Rebounds per Game", f"{safe_float(season_stats['reb']):.1f}",
                     f"Z-Score: {normalized_stats['reb_z'][0]:.2f}")
            st.metric("3-Point %", f"{safe_float(season_stats['fg3_pct']):.3f}",
                     f"Z-Score: {normalized_stats['fg3_pct_z'][0]:.2f}")
        
        with col3:
            st.metric("Assists per Game", f"{safe_float(season_stats['ast']):.1f}",
                     f"Z-Score: {normalized_stats['ast_z'][0]:.2f}")
            st.metric("Free Throw %", f"{safe_float(season_stats['ft_pct']):.3f}",
                     f"Z-Score: {normalized_stats['ft_pct_z'][0]:.2f}")
        
        with col4:
            st.metric("Minutes per Game", f"{parse_minutes(season_stats['min']):.1f}",
                     f"Z-Score: {normalized_stats['min_z'][0]:.2f}")
            st.metric("Games Played", f"{safe_float(season_stats['games_played'], 0):.0f}")
    else:
        st.warning(f"⚠️ No season statistics available for {display_season_formatted}. The player may not have played in this season or data is unavailable.")
    
    # Recent Game Performance
    st.header("📈 Recent Game Performance")
    
    if recent_games and len(recent_games) > 0:
        # Extract nested game data and flatten structure
        flattened_games = []
        for game in recent_games:
            flat_game = {
                'date': game.get('game', {}).get('date'),
                'pts': game.get('pts'),
                'reb': game.get('reb'),
                'ast': game.get('ast'),
                'fg_pct': game.get('fg_pct'),
                'fg3m': game.get('fg3m'),
                'min': game.get('min')
            }
            flattened_games.append(flat_game)
        
        games_df = pd.DataFrame(flattened_games)
        games_df['date'] = pd.to_datetime(games_df['date'])
        
        # Convert all numeric columns to float to avoid NaN plotting errors
        numeric_cols = ['pts', 'reb', 'ast', 'fg_pct', 'fg3m', 'min']
        for col in numeric_cols:
            games_df[col] = pd.to_numeric(games_df[col], errors='coerce')
        
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
        
        # Add season averages as horizontal lines (convert to float, parse minutes from MM:SS)
        if season_stats:
            fig.add_hline(y=safe_float(season_stats['pts']), line_dash="dash", line_color="gray", row=1, col=1)
            fig.add_hline(y=safe_float(season_stats['reb']), line_dash="dash", line_color="gray", row=1, col=2)
            fig.add_hline(y=safe_float(season_stats['ast']), line_dash="dash", line_color="gray", row=2, col=1)
            fig.add_hline(y=parse_minutes(season_stats['min']), line_dash="dash", line_color="gray", row=2, col=2)
        
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
        # Get custom thresholds from session state or use defaults
        thresholds = st.session_state.get('custom_thresholds', {
            'pts': [10, 15, 20],
            'reb': [4, 6, 8, 10],
            'ast': [4, 6, 8, 10],
            'fg3m': [2, 3, 5]
        })
        
        alpha = st.session_state.get('alpha', 0.85)
        
        # Calculate dynamic thresholds based on player's season stats
        dynamic_thresholds = stats_engine.calculate_dynamic_thresholds(season_stats)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Fixed Thresholds Analysis")
            
            games_df = pd.DataFrame(recent_games)
            probability_results = model.calculate_inverse_frequency_probabilities(
                games_df, thresholds, alpha=alpha
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
                games_df, dynamic_thresholds, alpha=alpha
            )
            
            st.write("**Cool-off Probabilities at Dynamic Thresholds:**")
            
            # Check if we have small sample size
            n_games = games_df.shape[0] if not games_df.empty else 0
            if n_games < 10:
                st.info(f"ℹ️ Small sample size ({n_games} games) - Bayesian smoothing applied for robust estimates")
            
            for stat in ['pts', 'reb', 'ast']:
                if stat in dynamic_prob_results:
                    st.write(f"**{stat.upper()}:**")
                    for threshold, data in dynamic_prob_results[stat].items():
                        # Display Bayesian smoothed estimate if available
                        if data.get('bayesian_smoothed'):
                            bayes = data['bayesian_smoothed']
                            smoothed_inv_prob = 1 - bayes['smoothed_probability']
                            credible_int = f"[{1-bayes['credible_interval_upper']:.2f}, {1-bayes['credible_interval_lower']:.2f}]"
                            st.write(f"  - {threshold}: {smoothed_inv_prob:.3f} (Bayesian CI: {credible_int})")
                        else:
                            ci_display = ""
                            if 'ci_lower' in data and 'ci_upper' in data:
                                ci_display = f" (95% CI: [{data['ci_lower']:.2f}, {data['ci_upper']:.2f}])"
                            sig_marker = " *" if data.get('significant', False) else ""
                            st.write(f"  - {threshold}: {data['inverse_probability']:.3f}{ci_display}{sig_marker}")
    
    # Career Phase and Fatigue Analysis
    st.header("⚡ Career Phase & Fatigue Analysis")
    
    if recent_games and len(recent_games) >= 10:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Fatigue/Load Curve")
            
            # Flatten games data
            flattened_fatigue_games = []
            for game in recent_games:
                flat_game = {
                    'date': game.get('game', {}).get('date'),
                    'pts': game.get('pts'),
                    'min': game.get('min')
                }
                flattened_fatigue_games.append(flat_game)
            
            games_df = pd.DataFrame(flattened_fatigue_games)
            games_df['date'] = pd.to_datetime(games_df['date'])
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
    
    # Next Game Predictions
    st.header("🔮 Next Game Predictions")
    
    if recent_games and season_stats:
        # Check if career phase decay is enabled
        use_career_phase = st.session_state.get('use_career_phase', False)
        
        if use_career_phase:
            st.markdown("*Predictions with Career Phase Decay enabled (Advanced Settings)*")
        else:
            st.markdown("*Based on historical performance and custom thresholds from Advanced Settings*")
        
        # Get custom thresholds and calculate probabilities
        thresholds = st.session_state.get('custom_thresholds', {
            'pts': [10, 15, 20],
            'reb': [4, 6, 8, 10],
            'ast': [4, 6, 8, 10],
            'fg3m': [2, 3, 5]
        })
        
        alpha = st.session_state.get('alpha', 0.85)
        games_df = pd.DataFrame(recent_games)
        
        # Calculate probabilities based on settings
        if use_career_phase:
            # Determine career phase
            career_stats = player_info.get('career_stats', [])
            career_phase = stats_engine.calculate_career_phase(career_stats)
            
            # Get lambda parameters from session state
            lambda_params = st.session_state.get('lambda_params', {
                'early': 0.02,
                'peak': 0.05,
                'late': 0.08
            })
            
            # Use comprehensive model with career phase
            comprehensive_results = model.calculate_comprehensive_regression_model(
                games_df, season_stats, career_phase, thresholds, lambda_params
            )
            
            # Extract weighted frequencies for display
            probability_results = {}
            for stat in thresholds.keys():
                if stat in comprehensive_results:
                    probability_results[stat] = {}
                    for threshold, data in comprehensive_results[stat].items():
                        # Use career-weighted frequency if available
                        if 'career_weighted_frequency' in data:
                            weighted_freq = data['career_weighted_frequency']
                        else:
                            weighted_freq = data.get('weighted_frequency', 0)
                        
                        probability_results[stat][threshold] = {
                            'weighted_frequency': weighted_freq,
                            'n_games': data.get('n_games', 0),
                            'n_exceeds': data.get('n_exceeds', 0),
                            'bayesian_smoothed': data.get('bayesian_smoothed'),
                            'career_phase': career_phase,
                            'fatigue_adjustment': data.get('fatigue_adjustment', 1.0),
                            'minutes_adjustment': data.get('minutes_adjustment', 1.0)
                        }
            
            # Show career phase indicator
            phase_emoji = {"early": "🌱", "rising": "📈", "peak": "⭐", "late": "🌅", "unknown": "❓"}
            st.info(f"{phase_emoji.get(career_phase, '❓')} Career Phase: **{career_phase.title()}** - Predictions adjusted with decay parameters")
        else:
            # Use basic inverse-frequency model
            probability_results = model.calculate_inverse_frequency_probabilities(
                games_df, thresholds, alpha=alpha
            )
        
        # Display predictions in a grid
        col1, col2 = st.columns(2)
        
        with col1:
            # Points predictions
            if 'pts' in probability_results:
                st.subheader("🏀 Points")
                for threshold, data in sorted(probability_results['pts'].items()):
                    success_prob = data['weighted_frequency']
                    confidence = "High" if data['n_exceeds'] >= 5 else "Low"
                    
                    # Apply Bayesian smoothing if small sample
                    if data.get('bayesian_smoothed'):
                        bayes = data['bayesian_smoothed']
                        success_prob = bayes['smoothed_probability']
                        st.metric(
                            f"≥ {threshold} points",
                            f"{success_prob*100:.1f}%",
                            f"Confidence: {confidence} ({data['n_games']} games)"
                        )
                    else:
                        st.metric(
                            f"≥ {threshold} points", 
                            f"{success_prob*100:.1f}%",
                            f"Confidence: {confidence} ({data['n_games']} games)"
                        )
            
            # Assists predictions
            if 'ast' in probability_results:
                st.subheader("🎯 Assists")
                for threshold, data in sorted(probability_results['ast'].items()):
                    success_prob = data['weighted_frequency']
                    confidence = "High" if data['n_exceeds'] >= 5 else "Low"
                    
                    if data.get('bayesian_smoothed'):
                        success_prob = data['bayesian_smoothed']['smoothed_probability']
                    
                    st.metric(
                        f"≥ {threshold} assists",
                        f"{success_prob*100:.1f}%",
                        f"Confidence: {confidence} ({data['n_games']} games)"
                    )
        
        with col2:
            # Rebounds predictions
            if 'reb' in probability_results:
                st.subheader("💪 Rebounds")
                for threshold, data in sorted(probability_results['reb'].items()):
                    success_prob = data['weighted_frequency']
                    confidence = "High" if data['n_exceeds'] >= 5 else "Low"
                    
                    if data.get('bayesian_smoothed'):
                        success_prob = data['bayesian_smoothed']['smoothed_probability']
                    
                    st.metric(
                        f"≥ {threshold} rebounds",
                        f"{success_prob*100:.1f}%",
                        f"Confidence: {confidence} ({data['n_games']} games)"
                    )
            
            # 3-Pointers predictions
            if 'fg3m' in probability_results:
                st.subheader("🎯 3-Pointers")
                for threshold, data in sorted(probability_results['fg3m'].items()):
                    success_prob = data['weighted_frequency']
                    confidence = "High" if data['n_exceeds'] >= 5 else "Low"
                    
                    if data.get('bayesian_smoothed'):
                        success_prob = data['bayesian_smoothed']['smoothed_probability']
                    
                    st.metric(
                        f"≥ {threshold} threes",
                        f"{success_prob*100:.1f}%",
                        f"Confidence: {confidence} ({data['n_games']} games)"
                    )
        
        # Show interpretation guide
        with st.expander("ℹ️ How to Read Predictions"):
            st.markdown("""
            **Success Probability**: Historical frequency of achieving the threshold, weighted by recency.
            
            **Confidence Levels**:
            - **High**: Player achieved this threshold 5+ times (reliable estimate)
            - **Low**: Player achieved this threshold <5 times (less reliable, Bayesian smoothing applied)
            
            **Recency Weighting**: Recent games are weighted more heavily (α = {:.2f})
            
            **Note**: These predictions are based on historical patterns. Actual performance depends on matchup, health, and other factors.
            """.format(alpha))

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
