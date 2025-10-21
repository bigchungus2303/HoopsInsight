"""
Pick of the Day - High-confidence predictions for upcoming games
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

from services.picks import PickOfTheDayService, export_picks_csv, export_picks_json
from nba_api import NBAAPIClient


def show_pick_of_the_day_page(api_client: NBAAPIClient):
    """Display Pick of the Day page"""
    st.header("🎯 Pick of the Day")
    st.caption("Top 5 high-confidence picks (≥77% probability) per team for today's games")
    
    # Initialize service
    service = PickOfTheDayService(api_client)
    
    # Refresh players button (prominent location)
    if st.button("🔄 Refresh Data", type="primary", use_container_width=False, 
                 help="Refresh injury data and player pools from API"):
        service._player_cache.clear()
        api_client._injured_players_cache = None
        api_client._injury_cache_time = None
        st.success("✅ Injury data and player cache refreshed!")
        st.rerun()
    
    # Injury disclaimer
    st.info("""
    🏥 **Automatic Injury Detection**: Using real-time data from balldontlie API.  
    Players with status "Out" are automatically excluded. Cache refreshes every hour.
    """)
    
    # Check API key first
    if not api_client.api_key:
        st.error("❌ **NBA API Key Not Configured**")
        st.warning("""
        The Pick of the Day feature requires an API key to search for players.
        
        **Your Player Analysis works because it has the API key configured.**
        
        Please set your API key in one of these locations:
        
        1. **Streamlit Secrets** (Recommended):
           - Create/edit `.streamlit/secrets.toml`
           - Add: `[api]`
           - Add: `nba_api_key = "your-key-here"`
        
        2. **Environment Variable**:
           - Set `NBA_API_KEY` environment variable
           - Restart the app
        
        Then reload this page.
        """)
        return
    
    # Fixed settings (no sidebar controls)
    preset = "default"
    alpha = 0.85
    min_samples = 3
    use_opponent_filter = True
    season_year = 2024  # Use 2024 season data (most recent available)
    
    # Automatically get today's games (using game_date_local from schedule)
    try:
        schedule = service.load_schedule_csv()
        available_dates = sorted(schedule['game_date_local'].unique())
        
        # Get today's date in local time
        today = datetime.now().date()
        
        # Find today's games first, then next available
        next_game_date = None
        
        for date in available_dates:
            if date >= today:
                next_game_date = date
                break
        
        if next_game_date is None:
            st.info("📅 No upcoming games found in schedule")
            return
        
        selected_date = next_game_date
        team_search = ""  # No team filter
        
    except Exception as e:
        st.error(f"❌ Error loading schedule: {str(e)}")
        return
    
    # Main content
    st.divider()
    
    # Find games for selected date
    try:
        selected_datetime = datetime.combine(selected_date, datetime.min.time())
        games = service.find_games_for_date(selected_datetime)
        
        if not games:
            st.info(f"📅 No games scheduled for {selected_date.strftime('%B %d, %Y')}")
            st.caption("Try selecting a different date from the sidebar")
            return
        
        # Filter by team if specified
        if team_search:
            search_lower = team_search.lower()
            games = [
                g for g in games
                if search_lower in g['visitor_team'].lower() or
                   search_lower in g['home_team'].lower() or
                   search_lower in g['visitor_abbr'].lower() or
                   search_lower in g['home_abbr'].lower()
            ]
            
            if not games:
                st.warning(f"No games found matching '{team_search}'")
                return
        
        st.success(f"📅 **{len(games)} game(s)** on {selected_date.strftime('%A, %B %d, %Y')}")
        
        # Generate picks for all games
        all_game_picks = []
        
        with st.spinner("🔮 Generating picks... This may take a minute..."):
            progress_bar = st.progress(0)
            for i, game in enumerate(games):
                progress_bar.progress((i + 1) / len(games))
                
                st.caption(f"Processing {game['visitor_abbr']} @ {game['home_abbr']}...")
                
                game_picks = service.generate_game_picks(
                    game,
                    preset=preset,
                    alpha=alpha,
                    min_samples=min_samples,
                    season=season_year,
                    use_opponent_filter=use_opponent_filter
                )
                all_game_picks.append(game_picks)
            
            progress_bar.empty()
        
        # Display game cards
        for game_pick in all_game_picks:
            display_game_card(game_pick)
        
        # Export section
        st.divider()
        st.subheader("📥 Export Picks")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export CSV", use_container_width=True):
                csv_data = export_picks_csv(all_game_picks)
                if csv_data:
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"picks_{selected_date.strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No picks to export")
        
        with col2:
            if st.button("📋 Export JSON", use_container_width=True):
                json_data = export_picks_json(all_game_picks)
                if json_data:
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"picks_{selected_date.strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                else:
                    st.warning("No picks to export")
        
    except Exception as e:
        st.error(f"❌ Error generating picks: {str(e)}")
        import traceback
        with st.expander("🔍 Debug Info"):
            st.code(traceback.format_exc())


def display_game_card(game_pick: Dict):
    """Display a game card with picks for both teams"""
    game_info = game_pick['game_info']
    away_team = game_pick['away_team']
    home_team = game_pick['home_team']
    away_picks = game_pick['away_picks']
    home_picks = game_pick['home_picks']
    
    # Game header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    ">
        <h3 style="color: white; text-align: center; margin: 0;">
            {game_info['visitor_team']} @ {game_info['home_team']}
        </h3>
        <p style="color: white; text-align: center; margin: 5px 0; opacity: 0.9;">
            🏟️ {game_info['arena']}, {game_info['city']}, {game_info['state']}
        </p>
        <p style="color: white; text-align: center; margin: 5px 0; opacity: 0.8;">
            🕐 {game_info['tip_time']} | 📺 {game_info['broadcasters'] if game_info['broadcasters'] else 'TBD'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Team picks in two columns
    col_away, col_home = st.columns(2)
    
    with col_away:
        st.markdown(f"### 🛫 {away_team} - {game_info['visitor_team']}")
        if away_picks:
            for pick in away_picks:
                display_pick_card(pick, team_abbr=away_team)
        else:
            st.info("No picks available for this team")
    
    with col_home:
        st.markdown(f"### 🏠 {home_team} - {game_info['home_team']}")
        if home_picks:
            for pick in home_picks:
                display_pick_card(pick, team_abbr=home_team)
        else:
            st.info("No picks available for this team")
    
    st.divider()


def display_pick_card(pick: Dict, team_abbr: str):
    """Display a single pick card using Streamlit components"""
    stat_icons = {
        'pts': '🏀',
        'reb': '💪',
        'ast': '🎯',
        'fg3m': '🎯'
    }
    
    stat_names = {
        'pts': 'Points',
        'reb': 'Rebounds',
        'ast': 'Assists',
        'fg3m': '3-Pointers'
    }
    
    icon = stat_icons.get(pick['stat'], '📊')
    stat_name = stat_names.get(pick['stat'], pick['stat'].upper())
    
    # Determine confidence color and styling
    prob = pick['probability']
    if prob >= 0.7:
        border_color = "green"
        confidence_text = "HIGH"
    elif prob >= 0.5:
        border_color = "orange"
        confidence_text = "MEDIUM"
    else:
        border_color = "red"
        confidence_text = "LOW"
    
    # Use container with border
    with st.container():
        # Create colored box using columns for border effect
        st.markdown(f"**{icon} {pick['player_name']}** — {stat_name} ≥ {pick['threshold']}")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### {prob*100:.1f}%")
        with col2:
            if prob >= 0.77:
                st.success(f"✅ {confidence_text}")
            elif prob >= 0.5:
                st.warning(f"⚠️ {confidence_text}")
            else:
                st.error(f"❌ {confidence_text}")
        
        # Badges
        if pick['badges']:
            st.caption(" | ".join(pick['badges']))
        
        # Rationale
        st.info(f"💡 {pick['rationale']}")
        
        # Metadata
        st.caption(f"📊 Based on {pick['n_games']} games | α={pick['alpha']:.2f}")
        
        st.divider()


if __name__ == "__main__":
    # For testing purposes
    api_client = NBAAPIClient()
    show_pick_of_the_day_page(api_client)

