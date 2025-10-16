import requests
import time
import os
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta
from database import NBADatabase

class NBAAPIClient:
    """Client for interacting with the balldontlie.io NBA API"""
    
    def __init__(self):
        self.base_url = "https://api.balldontlie.io/v1"
        self.nba_base_url = "https://api.balldontlie.io/nba/v1"  # New NBA API format
        self.api_key = os.getenv("NBA_API_KEY", "")  # API key from environment
        self.headers = {"Authorization": self.api_key} if self.api_key else {}  # Direct API key, not Bearer
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.db = NBADatabase()
    
    def _make_request(self, endpoint: str, params: Dict = None, max_retries: int = 3) -> Dict:
        """Make API request with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    response.raise_for_status()
            
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"API request failed after {max_retries} attempts: {str(e)}")
                time.sleep(1)
        
        return {}
    
    def _filter_played_games(self, games: List[Dict]) -> List[Dict]:
        """Filter out games where player didn't play (DNP, injured, etc.)"""
        played_games = []
        
        for game in games:
            min_played = game.get('min', '0')
            # Parse minutes if it's in MM:SS format
            if ':' in str(min_played):
                min_parts = str(min_played).split(':')
                if len(min_parts) == 2 and min_parts[0].isdigit():
                    min_value = int(min_parts[0])
                else:
                    min_value = 0
            else:
                min_value = float(min_played) if min_played and str(min_played).replace('.', '').isdigit() else 0
            
            # Include game if player had minutes or any stats
            has_stats = (
                min_value > 0 or 
                game.get('pts', 0) > 0 or 
                game.get('reb', 0) > 0 or 
                game.get('ast', 0) > 0
            )
            
            if has_stats:
                played_games.append(game)
        
        return played_games
    
    def search_players(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for players by name"""
        try:
            # Try cache first
            cached_players = self.db.search_cached_players(query)
            if cached_players and len(cached_players) >= 3:
                return cached_players[:limit]
            
            # Fetch from API
            params = {
                'search': query,
                'per_page': limit
            }
            response = self._make_request("players", params)
            players = response.get('data', [])
            
            # Cache players
            for player in players:
                self.db.cache_player(player)
            
            return players
        except Exception as e:
            print(f"Error searching players: {e}")
            return []
    
    def get_player_info(self, player_id: int) -> Optional[Dict]:
        """Get detailed player information"""
        try:
            response = self._make_request(f"players/{player_id}")
            return response.get('data')
        except Exception as e:
            print(f"Error getting player info: {e}")
            return None
    
    def get_season_stats(self, player_id: int, season: int, postseason: bool = False) -> Optional[Dict]:
        """Get season averages for a player"""
        try:
            # Try cache first
            cached_stats = self.db.get_season_stats(player_id, season, postseason=postseason)
            if cached_stats:
                return cached_stats
            
            # Use old v1 API with SINGULAR parameters
            params = {
                'player_id': player_id,  # Singular!
                'season': season,         # Singular!
                'postseason': postseason  # Boolean for playoff vs regular season
            }
            
            response = self._make_request("season_averages", params)
            data = response.get('data', [])
            
            if data:
                stats = data[0]
                # Cache the stats
                self.db.cache_season_stats(player_id, season, stats, postseason=postseason)
                return stats
            
            return None
            
        except Exception as e:
            print(f"Error getting season stats: {e}")
            return None
    
    def get_recent_games(self, player_id: int, limit: int = 20, season: int = None, postseason: bool = False) -> List[Dict]:
        """Get recent games for a player"""
        try:
            # If no season specified, use current season
            if season is None:
                current_year = datetime.now().year
                season = current_year if datetime.now().month >= 10 else current_year - 1
            
            # Try cache first with season filter
            cached_games = self.db.get_game_stats(player_id, limit, season=season, postseason=postseason)
            if cached_games and len(cached_games) >= min(5, limit):
                # Filter cached games too - only return games where player actually played
                filtered_cached = self._filter_played_games(cached_games)
                if len(filtered_cached) >= min(5, limit):
                    return filtered_cached[:limit]
                # If not enough played games in cache, fetch fresh data below
            
            # Fetch from API for specific season - stats endpoint REQUIRES array notation
            # Request MORE games than limit to ensure we get the most recent ones after sorting
            params = {
                'player_ids[]': player_id,     # Array notation required!
                'seasons[]': season,           # Array notation required!
                'postseason': postseason,      # Boolean for playoff vs regular season
                'per_page': 100  # Get up to 100 games to ensure we capture the full season
            }
            
            response = self._make_request("stats", params)
            games = response.get('data', [])
            
            # Filter out games where player didn't play (DNP, injured, etc.)
            played_games = self._filter_played_games(games)
            
            # Sort by date descending to get most recent games first
            played_games.sort(key=lambda x: x.get('game', {}).get('date', ''), reverse=True)
            
            # Cache ALL games (including DNP) for the season
            self.db.cache_game_stats(player_id, games, postseason=postseason)
            
            # Return only the requested number of most recent PLAYED games
            return played_games[:limit]
            
        except Exception as e:
            print(f"Error getting recent games: {e}")
            return []
    
    def get_career_stats(self, player_id: int, postseason: bool = False) -> List[Dict]:
        """Get career statistics for a player across multiple seasons"""
        try:
            all_seasons = []
            
            # Get season averages for recent years (2020-2025) using old v1 API with SINGULAR parameters
            for season in range(2020, 2026):
                params = {
                    'player_id': player_id,  # Singular!
                    'season': season,         # Singular!
                    'postseason': postseason  # Boolean for playoff vs regular season
                }
                
                try:
                    response = self._make_request("season_averages", params)
                    data = response.get('data', [])
                    if data:
                        all_seasons.extend(data)
                except:
                    pass  # Skip seasons with no data
                
                time.sleep(0.1)  # Rate limiting
            
            return all_seasons
            
        except Exception as e:
            print(f"Error getting career stats: {e}")
            return []
    
    def get_team_stats(self, season: int) -> List[Dict]:
        """Get team statistics for league averages calculation"""
        try:
            params = {
                'seasons[]': season,
                'per_page': 100
            }
            
            response = self._make_request("season_averages", params)
            return response.get('data', [])
            
        except Exception as e:
            print(f"Error getting team stats: {e}")
            return []
    
    def get_league_averages(self, season: int) -> Dict:
        """Calculate league averages for a given season"""
        try:
            # Try cache first
            cached_averages = self.db.get_league_averages(season)
            if cached_averages:
                return cached_averages
            
            # Get all player season averages
            all_players = []
            page = 1
            
            while True:
                params = {
                    'seasons[]': season,
                    'per_page': 100,
                    'page': page
                }
                
                response = self._make_request("season_averages", params)
                data = response.get('data', [])
                
                if not data:
                    break
                    
                all_players.extend(data)
                
                # Check if there are more pages
                meta = response.get('meta', {})
                if page >= meta.get('total_pages', 1):
                    break
                    
                page += 1
                time.sleep(0.1)  # Rate limiting
            
            if not all_players:
                return self._get_default_league_averages()
            
            # Calculate averages
            df = pd.DataFrame(all_players)
            
            # Filter out players with very low games played
            df = df[df['games_played'] >= 20]
            
            league_averages = {
                'pts': df['pts'].mean(),
                'reb': df['reb'].mean(),
                'ast': df['ast'].mean(),
                'fg_pct': df['fg_pct'].mean(),
                'fg3_pct': df['fg3_pct'].mean(),
                'ft_pct': df['ft_pct'].mean(),
                'min': df['min'].mean(),
                'pts_std': df['pts'].std(),
                'reb_std': df['reb'].std(),
                'ast_std': df['ast'].std(),
                'fg_pct_std': df['fg_pct'].std(),
                'fg3_pct_std': df['fg3_pct'].std(),
                'ft_pct_std': df['ft_pct'].std(),
                'min_std': df['min'].std()
            }
            
            # Cache the league averages
            self.db.cache_league_averages(season, league_averages)
            
            return league_averages
            
        except Exception as e:
            print(f"Error calculating league averages: {e}")
            return self._get_default_league_averages()
    
    def _get_default_league_averages(self) -> Dict:
        """Return default league averages if API fails"""
        return {
            'pts': 11.5,
            'reb': 4.2,
            'ast': 2.8,
            'fg_pct': 0.462,
            'fg3_pct': 0.367,
            'ft_pct': 0.783,
            'min': 20.5,
            'pts_std': 8.5,
            'reb_std': 3.2,
            'ast_std': 2.9,
            'fg_pct_std': 0.087,
            'fg3_pct_std': 0.112,
            'ft_pct_std': 0.125,
            'min_std': 9.8
        }
