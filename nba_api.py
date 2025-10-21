import requests
import time
import os
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta
from database import NBADatabase
from logger import get_logger
import config
from cache_sqlite import (
    init_db, cache_key, get_cached, set_cached, clear_cache,
    validate_games_schema, SCHEMA_VER
)

logger = get_logger(__name__)

# Initialize cache database
init_db()

class NBAAPIClient:
    """Client for interacting with the balldontlie.io NBA API"""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        # Try Streamlit secrets first, then environment variable
        try:
            import streamlit as st
            # Try both secret formats: root level and nested under [api]
            self.api_key = (
                st.secrets.get("NBA_API_KEY", "") or  # Root level
                st.secrets.get("api", {}).get("nba_api_key", "") or  # Nested
                os.getenv("NBA_API_KEY", "")  # Environment variable
            )
        except:
            self.api_key = os.getenv("NBA_API_KEY", "")
        
        self.headers = {"Authorization": self.api_key} if self.api_key else {}  # Direct API key, not Bearer
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.db = NBADatabase()
        self.api_call_count = 0  # Track API usage
        self.cache_hit_count = 0  # Track cache hits
        self._teams_cache = None  # Cache for team lookups
        self._injured_players_cache = None  # Cache for injury data
        self._injury_cache_time = None  # Timestamp of injury cache
        
        if not self.api_key:
            logger.warning("NBA_API_KEY not set - API calls may be rate limited")
    
    def _make_request(self, endpoint: str, params: Dict = None, max_retries: int = None) -> Dict:
        """Make API request with retry logic"""
        if max_retries is None:
            max_retries = config.API_MAX_RETRIES
            
        url = f"{self.base_url}/{endpoint}"
        
        # Convert boolean values to lowercase strings for API compatibility
        if params:
            params = {k: str(v).lower() if isinstance(v, bool) else v for k, v in params.items()}
        
        logger.debug(f"API request to {endpoint} with params: {params}")
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=config.API_TIMEOUT, verify=True)
                self.api_call_count += 1
                
                if response.status_code == 200:
                    logger.debug(f"API request successful: {endpoint}")
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    wait_time = config.API_RATE_LIMIT_BACKOFF_BASE ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API request failed with status {response.status_code}: {response.text[:200]}")
                    response.raise_for_status()
            
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise Exception(f"API request timed out after {max_retries} attempts")
                time.sleep(1)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"API request failed after {max_retries} attempts: {str(e)}")
                time.sleep(1)
        
        return {}
    
    def get_api_call_count(self) -> int:
        """Return the number of API calls made in this session"""
        return self.api_call_count
    
    def get_cache_hit_count(self) -> int:
        """Return the number of cache hits in this session"""
        return self.cache_hit_count
    
    def get_cache_stats(self) -> Dict:
        """Return cache statistics including hit rate"""
        total_requests = self.api_call_count + self.cache_hit_count
        hit_rate = (self.cache_hit_count / total_requests * 100) if total_requests > 0 else 0.0
        return {
            'api_calls': self.api_call_count,
            'cache_hits': self.cache_hit_count,
            'total_requests': total_requests,
            'cache_hit_rate': hit_rate
        }
    
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
            logger.error(f"Error searching players: {e}", exc_info=True)
            return []
    
    def get_player_info(self, player_id: int) -> Optional[Dict]:
        """Get detailed player information"""
        try:
            response = self._make_request(f"players/{player_id}")
            return response.get('data')
        except Exception as e:
            logger.error(f"Error getting player info for player_id {player_id}: {e}", exc_info=True)
            return None
    
    def get_season_stats(self, player_id: int, season: int, postseason: bool = False) -> Optional[Dict]:
        """Get season averages for a player"""
        try:
            # Try cache first
            cached_stats = self.db.get_season_stats(player_id, season, postseason=postseason)
            if cached_stats:
                self.cache_hit_count += 1
                logger.debug(f"Cache hit: season stats for player {player_id}, season {season}")
                return cached_stats
            
            # For playoffs, the season_averages endpoint doesn't support postseason parameter
            # We need to calculate averages from individual playoff games
            if postseason:
                # Get all playoff games for the season
                playoff_games = self.get_recent_games(player_id, limit=100, season=season, postseason=True)
                
                if not playoff_games:
                    return None
                
                # Calculate averages from playoff games
                # Helper to parse minutes from MM:SS format to decimal
                def parse_minutes(min_str):
                    if not min_str:
                        return 0.0
                    if isinstance(min_str, (int, float)):
                        return float(min_str)
                    if ':' in str(min_str):
                        parts = str(min_str).split(':')
                        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                            return int(parts[0]) + int(parts[1]) / 60.0
                    try:
                        return float(min_str)
                    except:
                        return 0.0
                
                # Helper to safely convert and calculate mean
                def safe_mean(values):
                    try:
                        nums = [float(v) if v is not None else 0.0 for v in values]
                        return sum(nums) / len(nums) if nums else 0.0
                    except:
                        return 0.0
                
                stats = {
                    'player_id': player_id,
                    'season': season,
                    'games_played': len(playoff_games),
                    'pts': safe_mean([g.get('pts', 0) for g in playoff_games]),
                    'reb': safe_mean([g.get('reb', 0) for g in playoff_games]),
                    'ast': safe_mean([g.get('ast', 0) for g in playoff_games]),
                    'fg_pct': safe_mean([g.get('fg_pct', 0) for g in playoff_games]),
                    'fg3_pct': safe_mean([g.get('fg3_pct', 0) for g in playoff_games]),
                    'ft_pct': safe_mean([g.get('ft_pct', 0) for g in playoff_games]),
                    'min': safe_mean([parse_minutes(g.get('min', 0)) for g in playoff_games])
                }
                
                # Cache the calculated stats
                self.db.cache_season_stats(player_id, season, stats, postseason=postseason)
                return stats
            else:
                # For regular season, use the season_averages endpoint
                params = {
                    'player_id': player_id,  # Singular!
                    'season': season          # Singular!
                }
                
                response = self._make_request("season_averages", params)
                data = response.get('data', [])
                
                if data:
                    stats = data[0]
                    # Parse minutes from MM:SS format to decimal
                    def parse_minutes(min_str):
                        if not min_str:
                            return 0.0
                        if isinstance(min_str, (int, float)):
                            return float(min_str)
                        if ':' in str(min_str):
                            parts = str(min_str).split(':')
                            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                                return int(parts[0]) + int(parts[1]) / 60.0
                        try:
                            return float(min_str)
                        except:
                            return 0.0
                    
                    # Convert minutes to float before caching
                    if 'min' in stats:
                        stats['min'] = parse_minutes(stats['min'])
                    
                    # Cache the stats
                    self.db.cache_season_stats(player_id, season, stats, postseason=postseason)
                    return stats
                
                return None
            
        except Exception as e:
            logger.error(f"Error getting season stats for player_id {player_id}, season {season}, postseason={postseason}: {e}", exc_info=True)
            return None
    
    def get_recent_games_smart(self, player_id: int, limit: int = 100, season: int = None, 
                               postseason: bool = False, min_games_threshold: int = 10) -> tuple[List[Dict], Dict]:
        """
        Get recent games with smart multi-season aggregation for season transitions
        
        Args:
            player_id: Player ID
            limit: Maximum number of games to return
            season: Target season
            postseason: Whether to get playoff games
            min_games_threshold: Minimum games before supplementing with previous season
            
        Returns:
            Tuple of (games_list, metadata_dict)
            metadata includes: current_season_games, prev_season_games, total_games
        """
        # Fetch current season games
        current_games = self.get_recent_games(player_id, limit=limit, season=season, postseason=postseason)
        
        metadata = {
            'current_season_games': len(current_games) if current_games else 0,
            'prev_season_games': 0,
            'seasons_used': [season],
            'supplemented': False
        }
        
        # If insufficient games, supplement with previous season
        current_count = len(current_games) if current_games else 0
        
        if current_count < min_games_threshold and season:
            prev_season = season - 1
            prev_games = self.get_recent_games(player_id, limit=100, season=prev_season, postseason=postseason)
            
            if prev_games and len(prev_games) > 0:
                # Combine and sort by date (most recent first)
                if current_games:
                    all_games = current_games + prev_games
                else:
                    all_games = prev_games
                
                all_games.sort(key=lambda x: x.get('game', {}).get('date', ''), reverse=True)
                
                # Limit to requested number
                combined_games = all_games[:limit]
                
                metadata['prev_season_games'] = len(prev_games)
                metadata['total_games'] = len(combined_games)
                metadata['seasons_used'] = [season, prev_season]
                metadata['supplemented'] = True
                
                return combined_games, metadata
        
        metadata['total_games'] = current_count
        return current_games if current_games else [], metadata
    
    def get_recent_games(self, player_id: int, limit: int = 20, season: int = None, postseason: bool = False) -> List[Dict]:
        """Get recent games for a player with schema-versioned caching"""
        try:
            # If no season specified, use current season
            if season is None:
                current_year = datetime.now().year
                season = current_year if datetime.now().month >= 10 else current_year - 1
            
            # Generate cache key
            namespace = "balldontlie:games"
            cache_params = {
                "player_id": player_id,
                "season": season,
                "postseason": postseason,
                "limit": limit
            }
            key = cache_key(namespace, cache_params, SCHEMA_VER)
            
            # Try cache first
            cached = get_cached(key)
            if cached:
                self.cache_hit_count += 1
                logger.debug(f"Cache hit: recent games for player {player_id}, season {season}")
                return cached.get("games", [])[:limit]
            
            # Fetch from API for specific season - stats endpoint REQUIRES array notation
            # Request MORE games than limit to ensure we get the most recent ones after sorting
            params = {
                'player_ids[]': player_id,     # Array notation required!
                'seasons[]': season,           # Array notation required!
                'postseason': postseason,      # Boolean for playoff vs regular season
                'per_page': 100  # Get up to 100 games to ensure we capture the full season
            }
            
            response = self._make_request("stats", params)
            raw_games = response.get('data', [])
            
            # Normalize games to include required schema fields
            normalized_games = []
            for raw_game in raw_games:
                game_info = raw_game.get('game', {})
                
                # Create normalized game with required fields for schema validation
                normalized = {
                    # Required fields for cache_sqlite schema
                    "id": game_info.get("id"),
                    "date": game_info.get("date"),
                    "home_team_id": game_info.get("home_team_id"),
                    "visitor_team_id": game_info.get("visitor_team_id"),
                    
                    # Preserve all original data for compatibility
                    "game": game_info,
                    "team": raw_game.get("team", {}),
                    "pts": raw_game.get("pts", 0),
                    "reb": raw_game.get("reb", 0),
                    "ast": raw_game.get("ast", 0),
                    "min": raw_game.get("min", "0"),
                    "fg_pct": raw_game.get("fg_pct", 0),
                    "fg3m": raw_game.get("fg3m", 0),
                    "fg3a": raw_game.get("fg3a", 0),
                    "stl": raw_game.get("stl", 0),
                    "blk": raw_game.get("blk", 0),
                    "turnover": raw_game.get("turnover", 0),
                }
                normalized_games.append(normalized)
            
            # Validate schema
            try:
                validate_games_schema(normalized_games)
            except ValueError as e:
                logger.error(f"Schema validation failed: {e}")
                # Clear cache and don't cache invalid data
                clear_cache()
                # Return empty if schema fails - don't propagate bad data
                return []
            
            # Filter out games where player didn't play (DNP, injured, etc.)
            played_games = self._filter_played_games(normalized_games)
            
            # Sort by date descending to get most recent games first
            played_games.sort(key=lambda x: x.get('game', {}).get('date', ''), reverse=True)
            
            # Cache the validated games
            payload = {"games": played_games}
            set_cached(key, payload, SCHEMA_VER)
            
            logger.info(f"Cached {len(played_games)} games for player {player_id}, season {season}")
            
            # Return only the requested number of most recent PLAYED games
            return played_games[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent games for player_id {player_id}, season {season}, postseason={postseason}: {e}", exc_info=True)
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
            logger.error(f"Error getting career stats for player_id {player_id}, postseason={postseason}: {e}", exc_info=True)
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
            logger.error(f"Error getting team stats for season {season}: {e}", exc_info=True)
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
            logger.error(f"Error calculating league averages for season {season}: {e}", exc_info=True)
            return self._get_default_league_averages()
    
    def _get_default_league_averages(self) -> Dict:
        """Return default league averages if API fails"""
        logger.warning("Using default league averages")
        return config.DEFAULT_LEAGUE_AVERAGES.copy()
    
    def get_teams(self) -> Dict[int, str]:
        """
        Get all NBA teams and return a dict mapping team_id to abbreviation
        Cached after first call for performance
        """
        if self._teams_cache is not None:
            return self._teams_cache
        
        try:
            response = self._make_request("teams", params={"per_page": 100})
            teams = response.get('data', [])
            
            # Create mapping of team_id -> abbreviation
            teams_dict = {}
            for team in teams:
                team_id = team.get('id')
                abbreviation = team.get('abbreviation')
                if team_id and abbreviation:
                    teams_dict[team_id] = abbreviation
            
            self._teams_cache = teams_dict
            logger.info(f"Loaded {len(teams_dict)} teams into cache")
            return teams_dict
            
        except Exception as e:
            logger.error(f"Error fetching teams: {e}", exc_info=True)
            return {}
    
    def get_injured_players(self, force_refresh: bool = False) -> List[int]:
        """
        Get list of player IDs currently out with injuries
        
        Args:
            force_refresh: Force refresh of injury data (default: use 1-hour cache)
            
        Returns:
            List of player IDs with status "Out"
        """
        # Check cache (1 hour expiry)
        if not force_refresh and self._injured_players_cache is not None:
            if self._injury_cache_time:
                cache_age = (datetime.now() - self._injury_cache_time).total_seconds()
                if cache_age < 3600:  # 1 hour cache
                    logger.debug(f"Using cached injury data ({cache_age:.0f}s old)")
                    return self._injured_players_cache
        
        try:
            logger.info("Fetching injury data from API...")
            injured_ids = []
            cursor = None
            
            # Fetch all pages of injury data
            for _ in range(10):  # Max 10 pages (safety limit)
                params = {"per_page": 100}
                if cursor:
                    params["cursor"] = cursor
                
                # Direct API call (injuries endpoint is at different base path)
                url = "https://api.balldontlie.io/nba/v1/player_injuries"
                try:
                    r = self.session.get(url, params=params, timeout=config.API_TIMEOUT)
                    r.raise_for_status()
                    response = r.json()
                    self.api_call_count += 1
                except Exception as e:
                    logger.error(f"Error fetching injuries: {e}")
                    response = None
                
                if response and 'data' in response:
                    # Filter for players with status "Out" (not Day-To-Day)
                    for injury in response['data']:
                        status = injury.get('status', '').lower()
                        if status == 'out':
                            player_id = injury.get('player', {}).get('id')
                            if player_id:
                                injured_ids.append(player_id)
                    
                    # Check for next page
                    cursor = response.get('meta', {}).get('next_cursor')
                    if not cursor:
                        break
                else:
                    break
            
            # Cache the result
            self._injured_players_cache = injured_ids
            self._injury_cache_time = datetime.now()
            
            logger.info(f"Found {len(injured_ids)} players with status 'Out'")
            return injured_ids
            
        except Exception as e:
            logger.error(f"Error fetching injury data: {e}")
            # Return empty list on error (fail gracefully)
            return []
    
    def get_all_teams_details(self) -> List[Dict]:
        """
        Get all NBA teams with full details (name, abbreviation, city, etc.)
        Returns a list of team dictionaries for autocomplete/search
        """
        # Generate cache key for teams
        namespace = "balldontlie:teams"
        key = cache_key(namespace, {}, "teams:v1")
        
        # Try cache first (24 hour TTL for teams - they rarely change)
        cached = get_cached(key, max_age_s=86400)
        if cached:
            logger.debug("Cache hit: teams data")
            return cached.get("teams", [])
        
        try:
            response = self._make_request("teams", params={"per_page": 100})
            teams = response.get('data', [])
            
            # Cache the teams data
            payload = {"teams": teams}
            set_cached(key, payload, "teams:v1")
            
            logger.info(f"Loaded {len(teams)} teams with full details")
            return teams
        except Exception as e:
            logger.error(f"Error fetching team details: {e}", exc_info=True)
            return []