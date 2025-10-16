import requests
import time
import os
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta

class NBAAPIClient:
    """Client for interacting with the balldontlie.io NBA API"""
    
    def __init__(self):
        self.base_url = "https://api.balldontlie.io/v1"
        self.api_key = os.getenv("NBA_API_KEY", "")  # API key from environment
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
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
    
    def search_players(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for players by name"""
        try:
            params = {
                'search': query,
                'per_page': limit
            }
            response = self._make_request("players", params)
            return response.get('data', [])
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
    
    def get_season_stats(self, player_id: int, season: int) -> Optional[Dict]:
        """Get season averages for a player"""
        try:
            params = {
                'player_ids[]': player_id,
                'seasons[]': season,
                'per_page': 100
            }
            
            response = self._make_request("season_averages", params)
            data = response.get('data', [])
            
            if data:
                return data[0]  # Return first (should be only) result
            return None
            
        except Exception as e:
            print(f"Error getting season stats: {e}")
            return None
    
    def get_recent_games(self, player_id: int, limit: int = 20) -> List[Dict]:
        """Get recent games for a player"""
        try:
            # Get games from current season
            current_year = datetime.now().year
            season = current_year if datetime.now().month >= 10 else current_year - 1
            
            params = {
                'player_ids[]': player_id,
                'seasons[]': season,
                'per_page': limit,
                'start_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            }
            
            response = self._make_request("stats", params)
            games = response.get('data', [])
            
            # Sort by date descending
            games.sort(key=lambda x: x.get('game', {}).get('date', ''), reverse=True)
            
            return games[:limit]
            
        except Exception as e:
            print(f"Error getting recent games: {e}")
            return []
    
    def get_career_stats(self, player_id: int) -> List[Dict]:
        """Get career statistics for a player across multiple seasons"""
        try:
            all_seasons = []
            
            # Get season averages for recent years (2020-2024)
            for season in range(2020, 2025):
                params = {
                    'player_ids[]': player_id,
                    'seasons[]': season,
                    'per_page': 100
                }
                
                response = self._make_request("season_averages", params)
                data = response.get('data', [])
                
                if data:
                    all_seasons.extend(data)
                
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
