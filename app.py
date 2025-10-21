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
from export_utils import export_player_stats_csv, export_player_stats_json
from database import NBADatabase
from error_handler import safe_api_call, show_loading, show_data_quality_warning

# Import modular components
# from components.api_dashboard import show_api_dashboard  # Hidden from UI
from components.advanced_settings import show_advanced_settings
from components.prediction_cards import show_all_predictions
from components.lambda_advisor import calculate_optimal_lambda

# Import pages (functions now defined inline)
# from pages.prediction_history import show_prediction_history_page
# from pages.season_report import show_season_report_page

def show_prediction_history_page(db):
    """Show prediction history page"""
    st.header("📊 Prediction History")
    st.info("Prediction history feature is being updated. Please check back later.")
    
def show_season_report_page(api_client, stats_engine, player_data):
    """Show season report page with descriptive statistics and visualizations"""
    st.header("📅 Season Report")
    
    if not player_data:
        st.info("👈 Search and load a player from the sidebar to view their season report")
        return
    
    player = player_data['player']
    season_stats = player_data.get('season_stats')
    all_games = player_data.get('all_games', [])
    season = player_data.get('season')
    is_postseason = player_data.get('is_postseason', False)
    
    # Player Header
    st.subheader(f"📊 {player['first_name']} {player['last_name']}")
    st.caption(f"{season}-{season+1} {'Playoffs' if is_postseason else 'Regular Season'}")
    
    if not all_games:
        st.warning("No games found for this player in the selected season.")
        return
    
    # Convert games to DataFrame
    import pandas as pd
    import plotly.graph_objects as go
    from datetime import datetime
    
    # Get team lookup dictionary for opponent abbreviations
    teams_lookup = api_client.get_teams()
    
    # Check if cached data has team information - if not, we need to fetch fresh
    if all_games and len(all_games) > 0:
        first_game = all_games[0]
        game_info = first_game.get('game', {})
        has_team_data = (
            game_info.get('home_team_id') is not None or 
            first_game.get('team', {}).get('id') is not None
        )
        
        if not has_team_data:
            st.warning("⚠️ Cached data missing team information. Click button below to clear cache and reload with opponent data.")
            if st.button("🔄 Clear Cache & Reload", key="clear_cache_for_opponents"):
                # Clear the player's game cache
                if player:
                    player_id = player.get('id')
                    # Delete cached games for this player
                    with api_client.db._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM game_stats WHERE player_id = ?", (player_id,))
                        conn.commit()
                    st.success("✅ Cache cleared! Please reload the player.")
                    st.rerun()
    
    games_data = []
    for game in all_games:
        game_info = game.get('game', {})
        game_date = game_info.get('date')
        if game_date:
            # The balldontlie API "stats" endpoint structure:
            # game['game'] = {id, date, season, status, period, time, postseason, home_team_score, visitor_team_score, home_team_id, visitor_team_id}
            # game['team'] = {id, abbreviation, city, conference, division, full_name, name}
            
            # Get team info from top level - this is the PLAYER's team
            player_team_data = game.get('team', {})
            player_team_id_from_game = player_team_data.get('id')
            
            # Get home/visitor team IDs from game info
            home_team_id = game_info.get('home_team_id')
            visitor_team_id = game_info.get('visitor_team_id')
            
            # Determine opponent using team lookup
            if player_team_id_from_game == home_team_id:
                # Player was home team, opponent is visitor
                home_away = 'vs'
                opponent_id = visitor_team_id
            elif player_team_id_from_game == visitor_team_id:
                # Player was away team, opponent is home
                home_away = '@'
                opponent_id = home_team_id
            else:
                home_away = 'vs'
                opponent_id = None
            
            # Look up opponent abbreviation
            opponent = teams_lookup.get(opponent_id, 'N/A') if opponent_id else 'N/A'
            
            games_data.append({
                'date': pd.to_datetime(game_date),
                'opponent': f"{home_away} {opponent}",
                'pts': game.get('pts', 0),
                'reb': game.get('reb', 0),
                'ast': game.get('ast', 0),
                'fg3m': game.get('fg3m', 0),
                'fg3a': game.get('fg3a', 0),
                'min': game.get('min', '0'),
                'fg_pct': game.get('fg_pct', 0)
            })
    
    if not games_data:
        st.warning("No valid game data found.")
        return
    
    games_df = pd.DataFrame(games_data)
    games_df = games_df.sort_values('date')
    
    # Date Range Filter
    st.subheader("📅 Date Range Filter")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        filter_type = st.radio(
            "Filter By",
            options=["Full Season", "Monthly", "Custom Date Range"],
            index=0,
            horizontal=False
        )
    
    # Apply filters based on selection
    filtered_df = games_df.copy()
    
    if filter_type == "Monthly":
        with col2:
            games_df['month'] = games_df['date'].dt.to_period('M')
            available_months = games_df['month'].unique()
            month_options = [str(m) for m in sorted(available_months)]
            
            if month_options:
                selected_month = st.selectbox("Select Month", month_options)
                filtered_df = games_df[games_df['month'] == pd.Period(selected_month)]
    
    elif filter_type == "Custom Date Range":
        min_date = games_df['date'].min().date()
        max_date = games_df['date'].max().date()
        
        with col2:
            start_date = st.date_input(
                "From",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="start_date_report"
            )
        
        with col3:
            end_date = st.date_input(
                "To",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="end_date_report"
            )
        
        # Filter by date range
        filtered_df = games_df[
            (games_df['date'].dt.date >= start_date) & 
            (games_df['date'].dt.date <= end_date)
        ]
    
    if filtered_df.empty:
        st.warning("No games found in the selected date range.")
        return
    
    st.divider()
    
    # Descriptive Statistics
    st.subheader("📊 Descriptive Statistics")
    
    stats_to_analyze = ['pts', 'reb', 'ast', 'fg3m', 'min']
    stat_labels = {
        'pts': 'Points',
        'reb': 'Rebounds',
        'ast': 'Assists',
        'fg3m': '3-Pointers Made',
        'min': 'Minutes Played'
    }
    
    # Convert minutes to numeric if string
    if filtered_df['min'].dtype == 'object':
        filtered_df['min'] = pd.to_numeric(filtered_df['min'].str.replace(':', '.').str[:5], errors='coerce')
    
    # Display metrics in grid
    cols = st.columns(5)
    for idx, stat in enumerate(stats_to_analyze):
        with cols[idx]:
            mean_val = filtered_df[stat].mean()
            st.metric(
                stat_labels[stat],
                f"{mean_val:.1f}",
                delta=None
            )
    
    # Detailed statistics table
    with st.expander("📈 View Detailed Statistics"):
        stats_summary = []
        for stat in stats_to_analyze:
            stats_summary.append({
                'Stat': stat_labels[stat],
                'Mean': f"{filtered_df[stat].mean():.2f}",
                'Median': f"{filtered_df[stat].median():.2f}",
                'Std Dev': f"{filtered_df[stat].std():.2f}",
                'Min': f"{filtered_df[stat].min():.2f}",
                'Max': f"{filtered_df[stat].max():.2f}",
                'Games': len(filtered_df)
            })
        
        st.dataframe(pd.DataFrame(stats_summary), use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Line Charts
    st.subheader("📈 Performance Trends")
    
    for stat in ['pts', 'reb', 'ast', 'fg3m']:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df[stat],
            mode='lines+markers',
            name=stat_labels[stat],
            line=dict(width=2),
            marker=dict(size=6)
        ))
        
        # Add mean line
        mean_val = filtered_df[stat].mean()
        fig.add_hline(
            y=mean_val,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Avg: {mean_val:.1f}",
            annotation_position="right"
        )
        
        fig.update_layout(
            title=f"{stat_labels[stat]} Over Time",
            xaxis_title="Date",
            yaxis_title=stat_labels[stat],
            hovermode='x unified',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Monthly Comparison (if full season view)
    if filter_type == "Full Season" and len(filtered_df) > 5:
        st.subheader("📊 Monthly Comparison")
        
        filtered_df['month'] = filtered_df['date'].dt.to_period('M').astype(str)
        monthly_avg = filtered_df.groupby('month')[['pts', 'reb', 'ast', 'fg3m']].mean().reset_index()
        
        fig = go.Figure()
        
        for stat in ['pts', 'reb', 'ast', 'fg3m']:
            fig.add_trace(go.Bar(
                x=monthly_avg['month'],
                y=monthly_avg[stat],
                name=stat_labels[stat]
            ))
        
        fig.update_layout(
            title="Monthly Average Statistics",
            xaxis_title="Month",
            yaxis_title="Average Value",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
    
    # Game Log with Anomaly Detection
    st.subheader("🎮 Game Log & Anomalies")
    
    # Detect anomalies
    anomalies = []
    for idx, row in filtered_df.iterrows():
        # Check for DNP or very low minutes
        if row['min'] < 5:
            anomalies.append({
                'date': row['date'],
                'opponent': row['opponent'],
                'type': '🔴 DNP/Low Minutes',
                'detail': f"Only {row['min']:.1f} minutes played"
            })
        
        # Check for statistical outliers (> 2 std dev)
        for stat in ['pts', 'reb', 'ast', 'fg3m']:
            mean = filtered_df[stat].mean()
            std = filtered_df[stat].std()
            
            if abs(row[stat] - mean) > 2 * std:
                if row[stat] > mean:
                    anomalies.append({
                        'date': row['date'],
                        'opponent': row['opponent'],
                        'type': f'🔥 High {stat_labels[stat]}',
                        'detail': f"{row[stat]:.0f} {stat} (avg: {mean:.1f})"
                    })
                else:
                    anomalies.append({
                        'date': row['date'],
                        'opponent': row['opponent'],
                        'type': f'❄️ Low {stat_labels[stat]}',
                        'detail': f"{row[stat]:.0f} {stat} (avg: {mean:.1f})"
                    })
    
    # Show anomalies
    if anomalies:
        st.info(f"**🔍 {len(anomalies)} anomalies detected**")
        anomaly_df = pd.DataFrame(anomalies)
        anomaly_df['date'] = pd.to_datetime(anomaly_df['date']).dt.strftime('%m/%d/%Y')
        st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No significant anomalies detected")
    
    # Full game log
    with st.expander("📋 View All Games"):
        display_df = filtered_df.copy()
        display_df['date'] = display_df['date'].dt.strftime('%m/%d/%Y')
        display_df = display_df[['date', 'opponent', 'pts', 'reb', 'ast', 'fg3m', 'fg_pct', 'min']]
        # Convert FG% to percentage format
        display_df['fg_pct'] = display_df['fg_pct'] * 100
        display_df.columns = ['Date', 'Opponent', 'PTS', 'REB', 'AST', '3PM', 'FG%', 'MIN']
        display_df = display_df.sort_values('Date', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# Initialize session state
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None
if 'player_data' not in st.session_state:
    st.session_state.player_data = None
if 'comparison_player' not in st.session_state:
    st.session_state.comparison_player = None
if 'comparison_data' not in st.session_state:
    st.session_state.comparison_data = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Player Analysis'

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

# Feedback form in top right corner
col_title, col_feedback = st.columns([4, 1])

with col_title:
    st.title("🏀 NBA Player Performance Predictor")
    
    # Clickable disclaimer - prominent red text
    st.markdown("""
        <style>
        .disclaimer-text {
            color: #FF0000;
            font-weight: bold;
            font-size: 16px;
            text-align: center;
            padding: 5px;
            border: 2px solid #FF0000;
            border-radius: 5px;
            background-color: #FFF5F5;
            margin-bottom: 10px;
        }
        </style>
        <div class="disclaimer-text">
            ⚠️ DISCLAIMER - READ BEFORE USE ⚠️
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📄 Click to Read Full Disclaimer", expanded=False):
        st.markdown("""
## ⚠️ Important Notice

This application is provided for **informational and educational purposes only**.

### **Not Financial or Betting Advice**

The predictions, probabilities, and analyses provided:
- Are based on **historical statistical patterns** only
- Do **NOT** constitute financial, betting, or investment advice
- Should **NOT** be used as the sole basis for betting decisions
- Are **NOT** guaranteed to be accurate or profitable

### **No Warranty**

This software is provided "AS IS", without warranty of any kind.

### **Risk Acknowledgment**

- Sports betting involves **financial risk**
- Past performance does **NOT** guarantee future results  
- You may **lose money** if you use this for betting
- Always gamble responsibly and within your means

### **Data Accuracy**

- Data sourced from balldontlie.io (third-party)
- We do **NOT** guarantee accuracy or timeliness
- Statistical models are **approximations**
- Player performance depends on many unpredictable factors

### **User Responsibility**

By using this application, you acknowledge:
- You use this tool at your own risk
- You are responsible for your decisions
- You should conduct your own research
- You are of legal age for sports betting (if applicable)

### **Problem Gambling Resources**

If you or someone you know has a gambling problem:
- **National Helpline:** 1-800-522-4700
- **SAMHSA:** 1-800-662-4357
- Visit: www.ncpgambling.org

---

**By using this application, you accept full responsibility for your decisions.**
        """)

with col_feedback:
    with st.popover("💬 Feedback"):
        st.caption("Help us improve!")
        
        # Rate limiting check (persistent across sessions)
        # Use session ID as identifier (survives page refresh)
        import hashlib
        session_id = hashlib.md5(str(st.session_state).encode()).hexdigest()[:16]
        
        # Check database-based rate limit
        can_send = db.check_feedback_rate_limit(session_id, limit_seconds=60)
        
        if not can_send:
            st.warning("⏳ Please wait 60 seconds between feedback submissions")
            st.caption("This prevents spam and helps us manage feedback")
        else:
            feedback_name = st.text_input("Name (optional)", key="feedback_name", placeholder="Your name", max_chars=50)
            feedback_email = st.text_input("Email (optional)", key="feedback_email", placeholder="your@email.com", max_chars=100)
            feedback_message = st.text_area("Message", key="feedback_message", placeholder="Share your thoughts...", height=100, max_chars=500)
            
            # Show direct email link
            if feedback_message and len(feedback_message.strip()) > 0:
                # Sanitize inputs (prevent XSS/injection)
                import re
                import urllib.parse
                import html
                safe_name = re.sub(r'[^\w\s\-\.]', '', feedback_name or 'Anonymous')[:50]
                safe_email = re.sub(r'[^\w\s@\.\-]', '', feedback_email or 'Not provided')[:100]
                safe_message = html.escape(feedback_message[:500])  # HTML escape to prevent XSS
                
                # Create mailto link (URL-encoded for safety)
                subject = "HoopsInsight Feedback"
                body = f"From: {safe_name}\nEmail: {safe_email}\n\nMessage:\n{safe_message}"
                mailto_link = f"mailto:sam@aeo-insights.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                
                # Direct clickable link (sanitized inputs prevent XSS)
                st.markdown(f"""
                    <a href="{html.escape(mailto_link)}" target="_blank" style="
                        display: inline-block;
                        padding: 0.5rem 1rem;
                        background-color: #FF4B4B;
                        color: white;
                        text-decoration: none;
                        border-radius: 0.5rem;
                        font-weight: 600;
                        text-align: center;
                    ">📧 Send Feedback</a>
                """, unsafe_allow_html=True)
                st.caption("Click above to open your email client")
                
                # Track feedback submission (rate limiting - prevents spam)
                db.mark_feedback_sent(session_id)
            else:
                st.button("📧 Send Feedback", type="primary", disabled=True)
                st.caption("Please enter a message first")

st.divider()

# Route to different pages based on selection FIRST
current_page = st.session_state.current_page

if current_page == 'Prediction History':
    # Minimal sidebar for Prediction History
    with st.sidebar:
        # Navigation buttons
        st.subheader("Navigate")
        if st.button("🏀 Player Analysis", key="nav_to_analysis_from_history", use_container_width=True):
            st.session_state.current_page = 'Player Analysis'
            st.rerun()
        
        if st.button("📅 Season Report", key="nav_to_report_from_history", use_container_width=True):
            st.session_state.current_page = 'Season Report'
            st.rerun()
        
    
    # Show page
    try:
        show_prediction_history_page(db)
    except Exception as e:
        st.error(f"❌ Error loading Prediction History page: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    st.stop()

elif current_page == 'Season Report':
    # Season Report sidebar with own player search
    with st.sidebar:
        # Navigation buttons
        st.subheader("Navigate")
        if st.button("🏀 Player Analysis", key="nav_to_analysis_from_report", use_container_width=True):
            st.session_state.current_page = 'Player Analysis'
            st.rerun()
        
        if st.button("📊 Prediction History", key="nav_to_history_from_report", use_container_width=True):
            st.session_state.current_page = 'Prediction History'
            st.rerun()
        
        st.divider()
        
        # Player search for Season Report
        st.subheader("Select Player")
        report_search = st.text_input("Search Player", placeholder="Type player name...", key="report_search")
        
        # Season selection for report
        season_years = list(range(2024, 2019, -1))
        season_display = {year: f"{year}-{year+1}" for year in season_years}
        
        report_season_display = st.selectbox(
            "Season", 
            options=[season_display[year] for year in season_years],
            index=0,
            key="report_season"
        )
        report_season = int(report_season_display.split('-')[0])
        
        report_season_type = st.radio(
            "Type",
            options=["Regular Season", "Playoffs"],
            index=0,
            horizontal=True,
            key="report_season_type"
        )
        report_is_postseason = (report_season_type == "Playoffs")
        
        # Search and load player for report
        if report_search and len(report_search) >= 2:
            players = api_client.search_players(report_search)
            
            if players:
                player_options = {f"{p['first_name']} {p['last_name']} ({p['team']['abbreviation']})": p for p in players}
                selected_name = st.selectbox("Select Player", list(player_options.keys()), key="report_player_selector")
                
                if st.button("Load for Report", key="load_report_player"):
                    player = player_options[selected_name]
                    
                    with show_loading(f"Loading {player['first_name']} {player['last_name']}..."):
                        # Fetch data specifically for Season Report
                        season_stats = safe_api_call(
                            api_client.get_season_stats,
                            player['id'], report_season,
                            postseason=report_is_postseason,
                            default_return=None
                        )
                        
                        all_games = safe_api_call(
                            api_client.get_recent_games,
                            player['id'],
                            limit=100,  # Get all games for season report
                            season=report_season,
                            postseason=report_is_postseason,
                            default_return=[]
                        )
                        
                        career_stats = safe_api_call(
                            api_client.get_career_stats,
                            player['id'],
                            postseason=report_is_postseason,
                            default_return=[]
                        )
                        
                        # Store in separate session state for report
                        st.session_state.report_player_data = {
                            'player': player,
                            'season_stats': season_stats,
                            'all_games': all_games,
                            'career_stats': career_stats,
                            'season': report_season,
                            'is_postseason': report_is_postseason
                        }
                        
                        st.success(f"✅ Loaded {player['first_name']} {player['last_name']}!")
                        st.rerun()
        
        st.divider()
        
        # Show current loaded player
        if 'report_player_data' in st.session_state and st.session_state.report_player_data:
            player = st.session_state.report_player_data['player']
            st.info(f"**{player['first_name']} {player['last_name']}**")
            st.caption(f"Season: {st.session_state.report_player_data['season']}-{st.session_state.report_player_data['season']+1}")
            
            if st.button("🔄 Change Player", key="clear_report_player"):
                st.session_state.report_player_data = None
                st.rerun()
        
    
    # Show page with report-specific data
    try:
        report_data = st.session_state.get('report_player_data', None)
        show_season_report_page(api_client, stats_engine, report_data)
    except Exception as e:
        st.error(f"❌ Error loading Season Report page: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    st.stop()

# Player Analysis Page (default) - Full sidebar
with st.sidebar:
    # Navigation buttons to other pages
    st.subheader("Navigate")
    if st.button("📅 Season Report", key="nav_to_report", use_container_width=True):
        st.session_state.current_page = 'Season Report'
        st.rerun()
    
    if st.button("📊 Prediction History", key="nav_to_history", use_container_width=True):
        st.session_state.current_page = 'Prediction History'
        st.rerun()
    
    st.divider()
    
    st.subheader("Player Search")
    
    st.divider()
    
    # Favorites quick access
    favorites = db.get_favorites()
    if favorites:
        with st.expander("⭐ Favorites"):
            fav_season_years = list(range(2024, 2019, -1))
            fav_season_display = {year: f"{year}-{year+1}" for year in fav_season_years}
            
            fav_season_selected = st.selectbox(
                "Season for Favorites", 
                options=[fav_season_display[year] for year in fav_season_years],
                index=0,
                key="fav_season_selector"
            )
            # Extract the base year from display format
            fav_season = int(fav_season_selected.split('-')[0])
            
            fav_season_type = st.radio(
                "Type",
                options=["Regular Season", "Playoffs"],
                index=0,
                horizontal=True,
                key="fav_season_type"
            )
            fav_is_postseason = (fav_season_type == "Playoffs")
            
            for fav in favorites:
                if st.button(f"{fav['player_name']} ({fav['team_abbreviation']})", key=f"fav_{fav['player_id']}"):
                    # Load favorite player with error handling
                    with show_loading(f"Loading {fav['player_name']}..."):
                        try:
                            player = safe_api_call(
                                api_client.get_player_info,
                                fav['player_id'],
                                error_message=f"Unable to load player information for {fav['player_name']}"
                            )
                            
                            if player:
                                st.session_state.selected_player = player
                                st.session_state.selected_season = fav_season
                                st.session_state.is_postseason = fav_is_postseason
                                
                                season_stats = safe_api_call(
                                    api_client.get_season_stats,
                                    player['id'], fav_season,
                                    postseason=fav_is_postseason,
                                    default_return=None
                                )
                                recent_games = safe_api_call(
                                    api_client.get_recent_games,
                                    player['id'],
                                    limit=100, season=fav_season, postseason=fav_is_postseason,
                                    default_return=[]
                                )
                                career_stats = safe_api_call(
                                    api_client.get_career_stats,
                                    player['id'],
                                    postseason=fav_is_postseason,
                                    default_return=[]
                                )
                                
                                st.session_state.player_data = {
                                    'player': player,
                                    'season_stats': season_stats,
                                    'recent_games': recent_games,
                                    'career_stats': career_stats
                                }
                                st.success(f"✅ Loaded {fav['player_name']} successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Could not load {fav['player_name']}. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error loading player: {str(e)}")

    
    # Player search with autocomplete
    search_query = st.text_input("Search Player Name", placeholder="Type player name (e.g., LeBron)...", key="player_search")
    
    # Season selection (display as "2024-2025" format)
    current_year = datetime.now().year
    season_year = current_year if datetime.now().month >= 10 else current_year - 1
    # Default to 2024 season (2024-2025) since 2025 season data not available yet
    season_years = list(range(2024, 2019, -1))
    season_display = {year: f"{year}-{year+1}" for year in season_years}
    
    selected_season_display = st.selectbox(
        "Select Season", 
        options=[season_display[year] for year in season_years],
        index=0,
        key="season_selector"
    )
    # Extract the base year from the display format (e.g., "2024-2025" -> 2024)
    selected_season = int(selected_season_display.split('-')[0])
    
    # Season Type selection (Regular Season vs Playoffs)
    season_type = st.radio(
        "Season Type",
        options=["Regular Season", "Playoffs"],
        index=0,
        horizontal=True,
        key="season_type_selector"
    )
    is_postseason = (season_type == "Playoffs")
    
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
                player = player_options[selected_player_name]
                player_full_name = f"{player['first_name']} {player['last_name']}"
                
                with show_loading(f"Loading {player_full_name}..."):
                    try:
                        st.session_state.selected_player = player
                        st.session_state.selected_season = selected_season
                        st.session_state.is_postseason = is_postseason
                        
                        # Fetch comprehensive player data for selected season with error handling
                        season_stats = safe_api_call(
                            api_client.get_season_stats,
                            player['id'], selected_season,
                            postseason=is_postseason,
                            default_return=None,
                            error_message=f"Unable to load season statistics for {player_full_name}"
                        )
                        
                        recent_games = safe_api_call(
                            api_client.get_recent_games,
                            player['id'],
                            limit=100, season=selected_season, postseason=is_postseason,
                            default_return=[],
                            error_message=f"Unable to load recent games for {player_full_name}"
                        )
                        
                        career_stats = safe_api_call(
                            api_client.get_career_stats,
                            player['id'],
                            postseason=is_postseason,
                            default_return=[],
                            error_message=f"Unable to load career stats for {player_full_name}"
                        )
                        
                        st.session_state.player_data = {
                            'player': player,
                            'season_stats': season_stats,
                            'recent_games': recent_games,
                            'career_stats': career_stats
                        }
                        
                        st.success(f"✅ Successfully loaded {player_full_name}!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error loading player data: {str(e)}")
                        st.info("💡 Try selecting a different season or check your connection.")
        else:
            st.info("No players found. Try a different search term.")
    elif search_query and len(search_query) < 2:
        st.caption("Type at least 2 characters to search")
    
    st.divider()
    
    # Advanced Settings
    show_advanced_settings()
    
    st.divider()
    
    # Comparison player search
    st.header("Player Comparison")
    comparison_query = st.text_input("Search Comparison Player", placeholder="Enter second player name...")
    
    comp_season_years = list(range(2024, 2019, -1))
    comp_season_display = {year: f"{year}-{year+1}" for year in comp_season_years}
    
    comp_season_selected = st.selectbox(
        "Comparison Season", 
        options=[comp_season_display[year] for year in comp_season_years],
        index=0,
        key="comp_season_selector"
    )
    # Extract the base year from display format
    comp_season = int(comp_season_selected.split('-')[0])
    
    comp_season_type = st.radio(
        "Comparison Season Type",
        options=["Regular Season", "Playoffs"],
        index=0,
        horizontal=True,
        key="comp_season_type"
    )
    comp_is_postseason = (comp_season_type == "Playoffs")
    
    if comparison_query and len(comparison_query) >= 2:
        with st.spinner("Searching players..."):
            comparison_players = api_client.search_players(comparison_query)
        
        if comparison_players:
            comp_options = [f"{p['first_name']} {p['last_name']} ({p['team']['abbreviation']})" for p in comparison_players]
            selected_comp_idx = st.selectbox("Select Comparison Player", range(len(comp_options)), format_func=lambda x: comp_options[x])
            
            if st.button("Load Comparison Data"):
                comp_player = comparison_players[selected_comp_idx]
                comp_player_name = f"{comp_player['first_name']} {comp_player['last_name']}"
                
                with show_loading(f"Loading {comp_player_name}..."):
                    try:
                        st.session_state.comparison_player = comp_player
                        st.session_state.comparison_season = comp_season
                        st.session_state.comp_is_postseason = comp_is_postseason
                        
                        comp_season_stats = safe_api_call(
                            api_client.get_season_stats,
                            comp_player['id'], comp_season,
                            postseason=comp_is_postseason,
                            default_return=None
                        )
                        comp_recent_games = safe_api_call(
                            api_client.get_recent_games,
                            comp_player['id'],
                            limit=100, season=comp_season, postseason=comp_is_postseason,
                            default_return=[]
                        )
                        comp_career_stats = safe_api_call(
                            api_client.get_career_stats,
                            comp_player['id'],
                            postseason=comp_is_postseason,
                            default_return=[]
                        )
                        
                        st.session_state.comparison_data = {
                            'player': comp_player,
                            'season_stats': comp_season_stats,
                            'recent_games': comp_recent_games,
                            'career_stats': comp_career_stats
                        }
                        
                        st.success(f"✅ Loaded {comp_player_name} for comparison!")
                        
                    except Exception as e:
                        st.error(f"❌ Error loading comparison data: {str(e)}")

# Route to different pages based on selection
current_page = st.session_state.current_page

if current_page == 'Prediction History':
    # Show Prediction History page
    try:
        show_prediction_history_page(db)
    except Exception as e:
        st.error(f"❌ Error loading Prediction History page: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    st.stop()  # Stop execution - don't render player analysis

elif current_page == 'Season Report':
    # Show Season Report page
    try:
        show_season_report_page(api_client, stats_engine, st.session_state.player_data)
    except Exception as e:
        st.error(f"❌ Error loading Season Report page: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    st.stop()  # Stop execution - don't render player analysis

# Player Analysis Page (default) - Continue below if neither page above matched
# Main content area
if st.session_state.player_data is None:
    st.info("👈 Search and select a player from the sidebar to begin analysis")
    st.markdown("""
    ### Features:
    - **Player Search**: Find NBA players with autocomplete
    - **Season Statistics**: View per-game averages with z-score normalization
    - **Recent Performance**: Analyze all games from selected season with trend visualization
    - **Inverse-Frequency Model**: Calculate regression-to-mean probabilities
    - **Career Phase Weighting**: Adjust for early/peak/late career phases
    - **Player Comparison**: Side-by-side statistical analysis
    - **Minutes Trend Analysis**: Track playing time patterns and sustainability
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
    
    # Season Statistics
    display_season = st.session_state.get('selected_season', 2024)
    display_season_formatted = f"{display_season}-{display_season+1}"
    display_is_postseason = st.session_state.get('is_postseason', False)
    season_type_label = "Playoffs" if display_is_postseason else "Regular Season"
    
    col_header, col_export = st.columns([3, 1])
    with col_header:
        st.header(f"📊 Season Statistics ({display_season_formatted} {season_type_label})")
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
            st.metric("Points per Game", f"{safe_float(season_stats['pts']):.1f}")
            st.metric("Field Goal %", f"{safe_float(season_stats['fg_pct']) * 100:.1f}%")
        
        with col2:
            st.metric("Rebounds per Game", f"{safe_float(season_stats['reb']):.1f}")
            st.metric("3-Point %", f"{safe_float(season_stats['fg3_pct']) * 100:.1f}%")
        
        with col3:
            st.metric("Assists per Game", f"{safe_float(season_stats['ast']):.1f}")
            st.metric("Free Throw %", f"{safe_float(season_stats['ft_pct']) * 100:.1f}%")
        
        with col4:
            st.metric("Minutes per Game", f"{parse_minutes(season_stats['min']):.1f}")
            st.metric("Games Played", f"{safe_float(season_stats['games_played'], 0):.0f}")
    else:
        st.warning(f"⚠️ No season statistics available for {display_season_formatted}. The player may not have played in this season or data is unavailable.")
    
    # Recent Game Performance
    st.header("📈 Game Performance (Selected Season)")
    
    # Data quality check
    if not show_data_quality_warning(recent_games, "recent games", min_size=5):
        st.info("💡 **Suggestions:**")
        st.write("• Try selecting a different season")
        st.write("• Check if the player participated in this season type (Regular Season/Playoffs)")
        st.write("• Verify the player was active during the selected season")
    elif recent_games and len(recent_games) > 0:
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
        
        fig.update_layout(height=500, showlegend=False, title_text="Last 10 Games from Season (Dashed lines = Season Average)")
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"ℹ️ Showing last 10 games for visualization. All {len(recent_games)} games from season loaded for analysis.")
        
        # Recent games table
        display_games = games_df[['date', 'pts', 'reb', 'ast', 'fg_pct', 'fg3m', 'min']].copy()
        display_games['date'] = display_games['date'].dt.strftime('%m/%d')
        # Convert FG% to percentage format
        display_games['fg_pct'] = display_games['fg_pct'] * 100
        display_games.columns = ['Date', 'PTS', 'REB', 'AST', 'FG%', '3PM', 'MIN']
        st.dataframe(display_games, use_container_width=True)
    
    # Minutes Played Analysis (simplified from Career Phase & Fatigue Analysis)
    st.header("⚡ Minutes Played Analysis")
    
    if recent_games and len(recent_games) >= 10:
        # Flatten games data
        flattened_games = []
        for game in recent_games:
            flat_game = {
                'date': game.get('game', {}).get('date'),
                'pts': game.get('pts'),
                'min': game.get('min')
            }
            flattened_games.append(flat_game)
        
        games_df = pd.DataFrame(flattened_games)
        games_df['date'] = pd.to_datetime(games_df['date'])
        games_df = games_df.sort_values('date')
        
        # Analyze minutes played trend
        minutes_trend = model.analyze_minutes_trend(games_df)
        
        # Minutes Trend Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=games_df.index, y=games_df['min'],
                               mode='lines+markers', name='Minutes Played'))
        
        if minutes_trend['declining_trend']:
            fig.add_annotation(text="⚠️ Declining Minutes Detected", 
                             x=0.5, y=0.9, xref="paper", yref="paper",
                             showarrow=False, bgcolor="yellow")
        
        fig.update_layout(title="Minutes Played Trend", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Minutes Trend", 
                     "📉 Declining" if minutes_trend['declining_trend'] else "📊 Stable")
        with col2:
            st.metric("Sustainability Factor", 
                     f"{minutes_trend['sustainability_factor']:.3f}")
    
    # Next Game Predictions
    st.header("🔮 Next Game Predictions")
    
    if recent_games and season_stats:
        # Opponent Team Filter
        col1, col2 = st.columns([1, 3])
        with col1:
            filter_by_opponent = st.toggle("🏀 Filter by Opponent", value=False, help="Filter predictions based on performance against specific team")
        
        opponent_team = None
        filtered_recent_games = recent_games
        
        if filter_by_opponent:
            with col2:
                # Debug option and cache management
                col_debug1, col_debug2 = st.columns(2)
                with col_debug1:
                    show_debug = st.checkbox("🔍 Show Debug Info", value=False, help="Show detailed debugging information about loaded games")
                with col_debug2:
                    if st.button("🔄 Clear Cache", help="Clear ALL cached data (games, teams) and reload fresh from API"):
                        from cache_sqlite import clear_cache
                        clear_cache()
                        st.success("✅ Cache cleared! All cached data removed.")
                        st.info("💡 Click 'Load Player Data' in the sidebar to fetch fresh data with correct team information.")
                
                # Get all NBA teams for autocomplete
                all_teams = api_client.get_all_teams_details()
                
                # Create searchable team options
                if all_teams:
                    # Text input for search
                    opponent_search = st.text_input(
                        "Search Team",
                        placeholder="Type team name or abbreviation (e.g., Lakers, LAL)...",
                        help="Search for the opponent team",
                        key="opponent_search_input"
                    )
                    
                    # Filter teams based on search input
                    if opponent_search and len(opponent_search) >= 1:
                        search_lower = opponent_search.lower()
                        filtered_teams = [
                            team for team in all_teams
                            if (search_lower in team.get('abbreviation', '').lower() or
                                search_lower in team.get('full_name', '').lower() or
                                search_lower in team.get('name', '').lower() or
                                search_lower in team.get('city', '').lower())
                        ]
                        
                        if filtered_teams:
                            # Create dropdown with filtered teams
                            team_options = {
                                f"{team['full_name']} ({team['abbreviation']})": team['abbreviation']
                                for team in filtered_teams
                            }
                            
                            selected_team_display = st.selectbox(
                                "Select Team",
                                options=list(team_options.keys()),
                                key="opponent_team_selector"
                            )
                            
                            opponent_team_input = team_options[selected_team_display]
                        else:
                            st.info("No teams found. Try a different search term.")
                            opponent_team_input = None
                    else:
                        opponent_team_input = None
                        if not opponent_search:
                            st.caption("💡 Type at least 1 character to search")
                else:
                    # Fallback to old text input if API fails
                    opponent_team_input = st.text_input(
                        "Enter Opponent Team (e.g., LAL, BOS, GSW)",
                        placeholder="Type team abbreviation...",
                        help="Enter the 3-letter team abbreviation for the next opponent",
                        key="opponent_team_input_fallback"
                    )
                
                # Show teams from player's game history as reference
                teams_lookup = api_client.get_teams()
                opponents_set = set()
                for game in recent_games:
                    game_info = game.get('game', {})
                    player_team_data = game.get('team', {})
                    player_team_id = player_team_data.get('id')
                    
                    home_team_id = game_info.get('home_team_id')
                    visitor_team_id = game_info.get('visitor_team_id')
                    
                    # Determine opponent ID
                    if player_team_id == home_team_id:
                        opponent_id = visitor_team_id
                    elif player_team_id == visitor_team_id:
                        opponent_id = home_team_id
                    else:
                        opponent_id = None
                    
                    # Look up opponent abbreviation
                    if opponent_id and opponent_id in teams_lookup:
                        opponents_set.add(teams_lookup[opponent_id])
                
                opponents_list = sorted(list(opponents_set))
            
            # Process opponent filter when user enters a team
            if opponent_team_input and len(opponent_team_input.strip()) > 0:
                opponent_team = opponent_team_input.strip().upper()
                
                # Debug info collection
                debug_info = []
                
                # Filter games to only those against entered opponent (sorted by date, most recent first)
                opponent_games = []
                for game in recent_games:
                    game_info = game.get('game', {})
                    player_team_data = game.get('team', {})
                    player_team_id = player_team_data.get('id')
                    
                    home_team_id = game_info.get('home_team_id')
                    visitor_team_id = game_info.get('visitor_team_id')
                    
                    # Determine opponent ID
                    if player_team_id == home_team_id:
                        opponent_id = visitor_team_id
                    elif player_team_id == visitor_team_id:
                        opponent_id = home_team_id
                    else:
                        opponent_id = None
                    
                    # Look up opponent abbreviation
                    game_opponent = teams_lookup.get(opponent_id, 'N/A') if opponent_id else 'N/A'
                    
                    # Collect debug info
                    if show_debug:
                        debug_info.append({
                            'date': game_info.get('date', 'N/A'),
                            'player_team_id': player_team_id,
                            'home_team_id': home_team_id,
                            'visitor_team_id': visitor_team_id,
                            'opponent_id': opponent_id,
                            'opponent_abbr': game_opponent
                        })
                    
                    if game_opponent.upper() == opponent_team:
                        opponent_games.append(game)
                
                # Show debug information if enabled
                if show_debug:
                    with st.expander("🔍 Debug: All Loaded Games", expanded=True):
                        st.write(f"**Total games loaded:** {len(recent_games)}")
                        st.write(f"**Looking for opponent:** {opponent_team}")
                        st.write(f"**Games found vs {opponent_team}:** {len(opponent_games)}")
                        
                        if debug_info:
                            import pandas as pd
                            debug_df = pd.DataFrame(debug_info)
                            st.dataframe(debug_df, use_container_width=True)
                        else:
                            st.warning("No debug info collected. Make sure games are loaded.")
                        
                        # Show unique opponents found
                        unique_opponents = set([info['opponent_abbr'] for info in debug_info if info['opponent_abbr'] != 'N/A'])
                        st.write(f"**Unique opponents in loaded games:** {', '.join(sorted(unique_opponents))}")
                
                # Use ALL games against this opponent from the season
                if opponent_games:
                    # Sort by date to get most recent first
                    opponent_games.sort(key=lambda x: x.get('game', {}).get('date', ''), reverse=True)
                    filtered_recent_games = opponent_games  # Use ALL games vs opponent
                    
                    # Show success message with sample size info
                    st.success(f"✅ Using **ALL {len(filtered_recent_games)} game(s)** vs **{opponent_team}** from selected season")
                    
                    # Add sample size warning if too few games
                    if len(filtered_recent_games) < 3:
                        st.warning(f"⚠️ **Small sample size:** Only {len(filtered_recent_games)} game(s) available. Prediction reliability may be lower. Consider using general prediction instead.")
                    elif len(filtered_recent_games) < 2:
                        st.error(f"🚨 **Very small sample:** Only {len(filtered_recent_games)} game available. High uncertainty in predictions!")
                else:
                    # Check if the team abbreviation is valid by looking at the reference list
                    if opponent_team in opponents_list:
                        st.warning(f"⚠️ **{opponent_team}** is in history but not found in the selected season games. Try a different season or disable opponent filter.")
                    else:
                        st.info(f"💡 No games vs **{opponent_team}** found in this season. Predictions will use general performance across all games.")
                    filtered_recent_games = recent_games  # Fall back to all games
        
        # Check if career phase decay is enabled
        use_career_phase = st.session_state.get('use_career_phase', False)
        
        if use_career_phase:
            st.markdown("*Predictions with Career Phase Decay enabled (Advanced Settings)*")
        else:
            st.markdown("*Based on historical performance and custom thresholds from Advanced Settings*")
        
        # Get custom thresholds and calculate probabilities
        thresholds = st.session_state.get('custom_thresholds', {
            'pts': [20],
            'reb': [8],
            'ast': [6],
            'fg3m': [3]
        })
        
        alpha = st.session_state.get('alpha', 0.85)
        games_df = pd.DataFrame(filtered_recent_games)
        
        # Calculate probabilities based on settings
        if use_career_phase:
            # Determine career phase
            career_stats = player_info.get('career_stats', [])
            career_phase = stats_engine.calculate_career_phase(career_stats)
            
            # Auto-calculate optimal lambda parameters
            lambda_advice = calculate_optimal_lambda(
                player=player,
                career_stats=career_stats,
                recent_games=recent_games,
                season_stats=season_stats,
                career_phase=career_phase
            )
            
            # Get lambda parameters from session state (may be auto or manual)
            lambda_params = st.session_state.get('lambda_params', {
                'early': 0.02,
                'peak': 0.05,
                'late': 0.08
            })
            
            # Show clean lambda advisor panel
            current_lambda = lambda_params.get(career_phase, 0.05)
            
            # Check if using auto values
            using_auto = abs(current_lambda - lambda_advice['recommended']) < 0.005
            
            with st.container():
                # Compact recommendation display
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    phase_emoji = {"early": "🌱", "rising": "📈", "peak": "⭐", "late": "🌅", "unknown": "❓"}
                    st.info(f"{phase_emoji.get(career_phase, '❓')} **Career Phase:** {career_phase.title()}")
                
                with col2:
                    if using_auto:
                        st.success(f"🤖 **Using Auto λ:** {lambda_advice['recommended']:.3f}")
                    else:
                        st.warning(f"⚙️ **Manual λ:** {current_lambda:.3f} (Auto: {lambda_advice['recommended']:.3f})")
                
                with col3:
                    use_auto = st.button("✨ Auto", key="use_auto_lambda", help="Apply AI-recommended lambda values")
                
                if use_auto:
                    # Update session state with auto-calculated values
                    st.session_state.lambda_early_value = lambda_advice['early']
                    st.session_state.lambda_peak_value = lambda_advice['peak']
                    st.session_state.lambda_late_value = lambda_advice['late']
                    st.success(f"✅ Applied auto-calculated λ = {lambda_advice['recommended']:.3f}")
                    st.rerun()
                
                # Collapsible details
                with st.expander("📊 Lambda Analysis Details"):
                    st.caption(f"**Confidence:** {lambda_advice['confidence']}")
                    st.write(f"**Why λ = {lambda_advice['recommended']:.3f}?**")
                    st.caption(lambda_advice['reasoning'])
                    
                    if any(lambda_advice['adjustments'].values()):
                        st.divider()
                        adj_col1, adj_col2, adj_col3 = st.columns(3)
                        with adj_col1:
                            st.metric("Age Factor", f"{lambda_advice['adjustments']['age']:+.3f}")
                        with adj_col2:
                            st.metric("Variance Factor", f"{lambda_advice['adjustments']['variance']:+.3f}")
                        with adj_col3:
                            st.metric("Load Mgmt", f"{lambda_advice['adjustments']['load_management']:+.3f}")
                    
                    st.caption("💡 Adjust manually in Advanced Settings or click '✨ Auto' to apply recommendation")
            
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
            
        else:
            # Use basic inverse-frequency model
            probability_results = model.calculate_inverse_frequency_probabilities(
                games_df, thresholds, alpha=alpha
            )
        
        # Display predictions with alpha impact option
        col1, col2 = st.columns([1, 3])
        with col1:
            show_alpha_impact = st.checkbox("🔍 Show α Impact", value=False, help="Compare weighted vs unweighted probabilities to see alpha effect")
        
        # Show alpha impact comparison if enabled
        if show_alpha_impact:
            st.divider()
            st.subheader("🔍 Alpha (α) Impact Analysis")
            st.caption(f"Current α = {alpha:.2f} | Comparing Weighted vs Unweighted Probabilities")
            
            impact_data = []
            for stat, stat_results in probability_results.items():
                stat_display = {'pts': 'Points', 'reb': 'Rebounds', 'ast': 'Assists', 'fg3m': '3-Pointers'}
                for threshold, data in stat_results.items():
                    weighted = data.get('weighted_frequency', 0) * 100
                    unweighted = data.get('frequency', 0) * 100
                    difference = weighted - unweighted
                    
                    impact_data.append({
                        'Stat': stat_display.get(stat, stat),
                        'Threshold': f"≥{threshold}",
                        'Unweighted (α=1.00)': f"{unweighted:.1f}%",
                        'Weighted (α={:.2f})'.format(alpha): f"{weighted:.1f}%",
                        'Difference': f"{difference:+.1f}%",
                        'Impact': '🔥 Hot' if difference > 10 else '❄️ Cold' if difference < -10 else '⚖️ Neutral'
                    })
            
            if impact_data:
                import pandas as pd
                impact_df = pd.DataFrame(impact_data)
                st.dataframe(impact_df, use_container_width=True, hide_index=True)
                
                # Summary
                avg_difference = sum([abs(float(d['Difference'].replace('%','').replace('+',''))) for d in impact_data]) / len(impact_data)
                if avg_difference < 3:
                    st.info(f"⚖️ **Low Impact:** Average difference {avg_difference:.1f}% - Player has consistent performance. α changes won't affect predictions much.")
                elif avg_difference < 10:
                    st.success(f"📊 **Moderate Impact:** Average difference {avg_difference:.1f}% - α is having a noticeable effect on predictions.")
                else:
                    st.warning(f"🔥 **High Impact:** Average difference {avg_difference:.1f}% - Strong recent trend! α is significantly affecting predictions.")
            
            st.divider()
        
        # Show technical predictions with percentages
        show_all_predictions(probability_results)
        
        # Show interpretation guide
        with st.expander("ℹ️ How to Read Predictions"):
            st.markdown("""
            **📊 Prediction Guide:**
            - **Success Probability**: Historical frequency of achieving the threshold, weighted by recency.
            
            **Confidence Levels**:
            - **High**: Player achieved this threshold 5+ times (reliable estimate)
            - **Low**: Player achieved this threshold <5 times (less reliable, Bayesian smoothing applied)
            
            **Recency Weighting**: Recent games are weighted more heavily (α = {:.2f})
            
            **Note**: These predictions are based on historical patterns. Actual performance depends on matchup, health, and other factors.
            """.format(alpha))
        
        # Save predictions section
        st.divider()
        st.subheader("💾 Save Predictions for Tracking")
        st.caption("Save predictions to track accuracy over time")
        
        with st.expander("📝 Save These Predictions"):
            # Date picker for next game
            next_game_date = st.date_input(
                "Next game date",
                value=datetime.now() + timedelta(days=1),
                key="next_game_date_main"
            )
            
            # Select which predictions to save
            st.write("**Select predictions to save:**")
            
            saved_count = 0
            for stat_key in ['pts', 'reb', 'ast', 'fg3m']:
                if stat_key in probability_results:
                    stat_display = {'pts': 'Points', 'reb': 'Rebounds', 'ast': 'Assists', 'fg3m': '3-Pointers'}[stat_key]
                    st.write(f"**{stat_display}:**")
                    
                    cols = st.columns(len(probability_results[stat_key]))
                    for idx, (threshold, data) in enumerate(sorted(probability_results[stat_key].items())):
                        with cols[idx]:
                            save_this = st.checkbox(
                                f"≥{threshold}: {data['weighted_frequency']*100:.0f}%",
                                key=f"save_pred_{stat_key}_{threshold}",
                                value=False
                            )
                            
                            if save_this and st.button(f"💾 Save", key=f"btn_save_{stat_key}_{threshold}"):
                                prediction_id = db.save_prediction(
                                    player_id=player['id'],
                                    player_name=f"{player['first_name']} {player['last_name']}",
                                    game_date=next_game_date.strftime('%Y-%m-%d'),
                                    season=st.session_state.get('selected_season', 2024),
                                    stat_type=stat_key,
                                    threshold=threshold,
                                    predicted_probability=data['weighted_frequency'],
                                    confidence=data['prediction_confidence'] if 'prediction_confidence' in data else ("High" if data['n_exceeds'] >= 5 else "Low")
                                )
                                
                                if prediction_id:
                                    st.success(f"✅ Saved! (ID: {prediction_id})")
                                    saved_count += 1
                                else:
                                    st.error("❌ Failed to save")
            
            if saved_count > 0:
                st.info(f"💡 Go to **Prediction History** page to verify after the game!")

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
            st.metric("FG%", f"{stats1['fg_pct'] * 100:.1f}%")
    
    with col2:
        st.subheader(f"{player2['first_name']} {player2['last_name']}")
        if player2_data['season_stats']:
            stats2 = player2_data['season_stats']
            st.metric("PPG", f"{stats2['pts']:.1f}")
            st.metric("RPG", f"{stats2['reb']:.1f}")
            st.metric("APG", f"{stats2['ast']:.1f}")
            st.metric("FG%", f"{stats2['fg_pct'] * 100:.1f}%")
    
    # Comparative bar chart
    if player1_data['season_stats'] and player2_data['season_stats']:
        comparison_stats = ['pts', 'reb', 'ast', 'fg_pct', 'fg3_pct']
        
        # Convert percentages to proper format (multiply by 100)
        def get_stat_value(stats, stat):
            val = stats[stat]
            return val * 100 if stat in ['fg_pct', 'fg3_pct'] else val
        
        fig = go.Figure(data=[
            go.Bar(name=f"{player1['last_name']}", x=comparison_stats, 
                   y=[get_stat_value(player1_data['season_stats'], stat) for stat in comparison_stats],
                   marker_color='#1f77b4'),
            go.Bar(name=f"{player2['last_name']}", x=comparison_stats,
                   y=[get_stat_value(player2_data['season_stats'], stat) for stat in comparison_stats],
                   marker_color='#ff7f0e')
        ])
        
        fig.update_layout(barmode='group', title="Season Averages Comparison",
                         xaxis_title="Statistics", yaxis_title="Values")
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Data**: [balldontlie.io](https://balldontlie.io)")
with col2:
    with st.expander("📄 Legal"):
        st.markdown("""
        **This app is for entertainment and educational purposes only.**
        
        - ⚠️ Not financial or betting advice
        - 📊 Based on historical statistics only
        - 🎲 Past performance ≠ future results
        - ⚖️ Use at your own risk
        
        Problem gambling? Call 1-800-522-4700
        """)
with col3:
    st.caption("© 2025 AEO Insights")
