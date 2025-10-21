"""
Pick of the Day service - generates high-confidence predictions for upcoming games
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yaml
from pathlib import Path

from nba_api import NBAAPIClient
from models import InverseFrequencyModel
from statistics import StatisticsEngine


class PickOfTheDayService:
    """Service for generating Pick of the Day predictions"""
    
    def __init__(self, api_client: NBAAPIClient, schedule_path: str = "nba_2025_2026_schedule.csv"):
        self.api_client = api_client
        self.schedule_path = schedule_path
        self.model = InverseFrequencyModel()
        self.stats_engine = StatisticsEngine()
        self.config = self._load_config()
        self._schedule_df = None
        self._player_cache = {}  # Cache player pools to avoid repeated API calls
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        config_path = Path("pick_configs/picks.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Return default config if file doesn't exist
            return {
                'presets': {
                    'default': {
                        'pts': [20, 25, 30, 35, 40],
                        'ast': [5, 7, 10, 12, 15],
                        'reb': [6, 8, 10, 12, 14],
                        'fg3m': [2, 3, 4, 5, 6]
                    },
                    'conservative': {
                        'pts': [15, 20, 25, 30],
                        'ast': [4, 6, 8, 10],
                        'reb': [5, 7, 9, 11],
                        'fg3m': [1, 2, 3, 4]
                    },
                    'aggressive': {
                        'pts': [25, 30, 35, 40, 45],
                        'ast': [7, 10, 12, 15, 18],
                        'reb': [8, 10, 12, 14, 16],
                        'fg3m': [3, 4, 5, 6, 7]
                    }
                },
                'diversity': {
                    'require_distinct_stats': True,
                    'min_conf_gap_for_duplicate_stat': 0.05
                },
                'filters': {
                    'min_minutes_last5': 18,
                    'exclude_small_sample_under': 2
                }
            }
    
    def load_schedule_csv(self, path: Optional[str] = None) -> pd.DataFrame:
        """Load NBA schedule from CSV file"""
        if path is None:
            path = self.schedule_path
        
        if self._schedule_df is not None:
            return self._schedule_df
        
        df = pd.read_csv(path)
        # Parse dates - use game_date_local for matching games by date
        df['game_date_local'] = pd.to_datetime(df['game_date_local']).dt.date
        df['utc_date'] = pd.to_datetime(df['utc_date']).dt.date
        
        self._schedule_df = df
        return df
    
    def find_games_for_date(self, date_utc: datetime) -> List[Dict]:
        """
        Find all games scheduled for a specific date (using local game date)
        
        Args:
            date_utc: Target date
            
        Returns:
            List of game dictionaries with home/away teams and metadata
        """
        schedule = self.load_schedule_csv()
        
        # Filter games by game_date_local (the actual game date)
        if isinstance(date_utc, datetime):
            target_date = date_utc.date()
        else:
            target_date = date_utc
        
        games_on_date = schedule[schedule['game_date_local'] == target_date]
        
        # Convert to list of dictionaries
        games = []
        for _, row in games_on_date.iterrows():
            game = {
                'gid': row['gid'],
                'game_date': row['game_date_local'],
                'utc_date': row['utc_date'],
                'utc_time': row['utc_time'],
                'visitor_abbr': row['visitor_abbr'],
                'visitor_team': row['visitor_team'],
                'home_abbr': row['home_abbr'],
                'home_team': row['home_team'],
                'arena': row['arena'],
                'city': row['city'],
                'state': row['state'],
                'broadcasters': row['broadcasters_tv'],
                'tip_time': row['tip_et_time']
            }
            games.append(game)
        
        return games
    
    def select_player_pool(self, team_abbr: str, date_utc: datetime, k: int = 8, 
                          season: int = 2024) -> List[Dict]:
        """
        Select top K players from a team based on star player roster
        
        Args:
            team_abbr: Team abbreviation (e.g., 'LAL')
            date_utc: Target date for filtering
            k: Number of top players to return
            season: Season year
            
        Returns:
            List of player dictionaries with stats
        
        Note:
            Uses static roster of star players to avoid API search issues.
            Results are cached to avoid repeated API calls.
        """
        # Check if API key is set - fail fast if not
        if not self.api_client.api_key:
            print(f"ERROR: NBA_API_KEY not set - cannot search for players")
            return []
        
        # Check cache first
        cache_key = f"{team_abbr}_{season}"
        if cache_key in self._player_cache:
            return self._player_cache[cache_key]
        
        # Static roster of top players per team (FIRST NAMES ONLY for API search)
        team_rosters = {
            'ATL': ['Trae', 'Dejounte', 'Clint'],
            'BOS': ['Jayson', 'Jaylen', 'Kristaps', 'Derrick'],
            'BKN': ['Mikal', 'Cam', 'Nicolas'],
            'CHA': ['LaMelo', 'Miles', 'Brandon'],
            'CHI': ['Zach', 'DeMar', 'Nikola'],
            'CLE': ['Donovan', 'Darius', 'Jarrett', 'Evan'],
            'DAL': ['Luka', 'Kyrie', 'Dereck'],
            'DEN': ['Nikola', 'Jamal', 'Michael'],
            'DET': ['Cade', 'Jaden', 'Isaiah'],
            'GSW': ['Stephen', 'Klay', 'Draymond', 'Andrew'],
            'HOU': ['Alperen', 'Fred', 'Jalen', 'Jabari'],
            'IND': ['Tyrese', 'Pascal', 'Myles'],
            'LAC': ['Kawhi', 'Paul', 'James', 'Russell'],
            'LAL': ['LeBron', 'Anthony', 'Austin', 'D Angelo'],
            'MEM': ['Ja', 'Desmond', 'Jaren'],
            'MIA': ['Jimmy', 'Bam', 'Tyler'],
            'MIL': ['Giannis', 'Damian', 'Khris', 'Brook'],
            'MIN': ['Anthony', 'Karl-Anthony', 'Rudy'],
            'NOP': ['Zion', 'Brandon', 'CJ'],
            'NYK': ['Jalen', 'Julius', 'RJ', 'Mitchell'],
            'OKC': ['Shai', 'Chet', 'Jalen', 'Josh'],
            'ORL': ['Paolo', 'Franz', 'Wendell'],
            'PHI': ['Joel', 'Tyrese', 'Tobias'],
            'PHX': ['Kevin', 'Devin', 'Bradley', 'Jusuf'],
            'POR': ['Anfernee', 'Jerami', 'Deandre'],
            'SAC': ['De Aaron', 'Domantas', 'Kevin'],
            'SAS': ['Victor', 'Devin', 'Keldon'],
            'TOR': ['Scottie', 'Pascal', 'OG'],
            'UTA': ['Lauri', 'Jordan', 'Walker'],
            'WAS': ['Kyle', 'Jordan', 'Daniel']
        }
        
        roster = team_rosters.get(team_abbr, [])
        if not roster:
            return []
        
        try:
            active_players = []
            
            for player_name in roster[:k*2]:  # Try more than k to find k active
                try:
                    # Search for this specific player
                    players = self.api_client.search_players(player_name)
                    
                    if not players:
                        continue
                    
                    # Find player on the correct team
                    player = None
                    for p in players:
                        if p.get('team', {}).get('abbreviation', '').upper() == team_abbr.upper():
                            player = p
                            break
                    
                    if not player:
                        continue
                    
                    # Get recent games to verify they're active
                    recent_games = self.api_client.get_recent_games(
                        player['id'], 
                        limit=5, 
                        season=season, 
                        postseason=False
                    )
                    
                    if recent_games and len(recent_games) > 0:
                        # Calculate average minutes
                        total_mins = 0
                        valid_games = 0
                        for game in recent_games:
                            mins = game.get('min', 0)
                            if isinstance(mins, str) and ':' in mins:
                                parts = mins.split(':')
                                mins = int(parts[0]) + int(parts[1]) / 60
                            total_mins += float(mins) if mins else 0
                            valid_games += 1
                        
                        avg_mins = total_mins / valid_games if valid_games > 0 else 0
                        
                        if avg_mins >= 15:
                            player['avg_minutes'] = avg_mins
                            active_players.append(player)
                            
                            if len(active_players) >= k:
                                break
                except Exception:
                    continue
            
            # Sort by average minutes
            active_players.sort(key=lambda p: p.get('avg_minutes', 0), reverse=True)
            
            result = active_players[:k]
            self._player_cache[cache_key] = result
            return result
            
        except Exception as e:
            return []
    
    def build_candidate_markets(self, player: Dict, preset: str = 'default') -> List[Tuple[str, float]]:
        """
        Build candidate markets (stat + threshold) for a player
        
        Args:
            player: Player dictionary with stats
            preset: Market preset name (default/conservative/aggressive)
            
        Returns:
            List of (stat_type, threshold) tuples
        """
        preset_config = self.config['presets'].get(preset, self.config['presets']['default'])
        
        candidates = []
        for stat, thresholds in preset_config.items():
            for threshold in thresholds:
                candidates.append((stat, threshold))
        
        return candidates
    
    def predict_probability(self, player: Dict, stat: str, threshold: float, 
                           opponent_abbr: str, date_utc: datetime, alpha: float = 0.85,
                           season: int = 2025) -> Optional[Dict]:
        """
        Predict probability for a specific player/stat/threshold
        
        Args:
            player: Player dictionary
            stat: Stat type (pts/reb/ast/fg3m)
            threshold: Threshold value
            opponent_abbr: Opponent team abbreviation
            date_utc: Target date
            alpha: Recency weight
            season: Season year
            
        Returns:
            Prediction dictionary with probability, confidence, rationale
        """
        player_id = player['id']
        
        # Fetch recent games
        try:
            recent_games = self.api_client.get_recent_games(
                player_id, 
                limit=100, 
                season=season, 
                postseason=False
            )
        except Exception as e:
            return None
        
        if not recent_games or len(recent_games) == 0:
            return None
        
        # Filter by opponent if specified
        if opponent_abbr:
            teams_lookup = self.api_client.get_teams()
            opponent_games = []
            
            for game in recent_games:
                game_info = game.get('game', {})
                player_team_data = game.get('team', {})
                player_team_id = player_team_data.get('id')
                
                home_team_id = game_info.get('home_team_id')
                visitor_team_id = game_info.get('visitor_team_id')
                
                # Determine opponent
                if player_team_id == home_team_id:
                    opponent_id = visitor_team_id
                elif player_team_id == visitor_team_id:
                    opponent_id = home_team_id
                else:
                    continue
                
                game_opponent = teams_lookup.get(opponent_id, 'N/A') if opponent_id else 'N/A'
                
                if game_opponent.upper() == opponent_abbr.upper():
                    opponent_games.append(game)
            
            # Use opponent-specific games if available, otherwise all games
            if len(opponent_games) >= 3:
                games_to_analyze = opponent_games
            else:
                games_to_analyze = recent_games
        else:
            games_to_analyze = recent_games
        
        # Convert to DataFrame
        games_df = pd.DataFrame(games_to_analyze)
        
        # Calculate probability using inverse-frequency model
        thresholds = {stat: [threshold]}
        results = self.model.calculate_inverse_frequency_probabilities(
            games_df, thresholds, alpha=alpha
        )
        
        if stat not in results or threshold not in results[stat]:
            return None
        
        result = results[stat][threshold]
        
        # Build prediction dictionary
        prediction = {
            'player_id': player_id,
            'player_name': f"{player.get('first_name', '')} {player.get('last_name', '')}",
            'stat': stat,
            'threshold': threshold,
            'probability': result['weighted_frequency'],
            'confidence': result['n_exceeds'],
            'n_games': result['n_games'],
            'std': games_df[stat].std() if stat in games_df.columns else 0,
            'alpha': alpha,
            'badges': self._generate_badges(result, games_df, stat),
            'rationale': self._generate_rationale(result, stat, threshold, opponent_abbr)
        }
        
        return prediction
    
    def _generate_badges(self, result: Dict, games_df: pd.DataFrame, stat: str) -> List[str]:
        """Generate badges for a prediction (HOT, COLD, etc.)"""
        badges = []
        
        # Hot badge - recent performance above average
        if len(games_df) >= 5:
            recent_avg = games_df[stat].tail(5).mean()
            season_avg = games_df[stat].mean()
            if recent_avg > season_avg * 1.15:
                badges.append('🔥 HOT')
            elif recent_avg < season_avg * 0.85:
                badges.append('❄️ COLD')
        
        # High confidence badge
        if result['n_exceeds'] >= 10:
            badges.append('✅ HIGH CONFIDENCE')
        elif result['n_exceeds'] < 3:
            badges.append('⚠️ SMALL SAMPLE')
        
        # Opponent-boosted (if opponent filter applied)
        # This would be detected by comparing opponent vs general stats
        
        return badges
    
    def _generate_rationale(self, result: Dict, stat: str, threshold: float, 
                           opponent_abbr: Optional[str]) -> str:
        """Generate human-readable rationale for prediction"""
        prob = result['weighted_frequency']
        n_exceeds = result['n_exceeds']
        n_games = result['n_games']
        
        stat_names = {
            'pts': 'points',
            'reb': 'rebounds',
            'ast': 'assists',
            'fg3m': '3-pointers'
        }
        stat_name = stat_names.get(stat, stat)
        
        if opponent_abbr:
            context = f" vs {opponent_abbr}"
        else:
            context = ""
        
        if prob >= 0.7:
            return f"Strong history{context}: exceeded {threshold} {stat_name} in {n_exceeds}/{n_games} recent games"
        elif prob >= 0.5:
            return f"Moderate chance{context}: exceeded {threshold} {stat_name} in {n_exceeds}/{n_games} recent games"
        elif prob >= 0.3:
            return f"Below average{context}: exceeded {threshold} {stat_name} in only {n_exceeds}/{n_games} recent games"
        else:
            return f"Low probability{context}: rarely exceeds {threshold} {stat_name} ({n_exceeds}/{n_games} games)"
    
    def top_picks(self, predictions: List[Dict], n: int = 5, 
                 require_distinct: bool = True, min_gap: float = 0.05, 
                 min_probability: float = 0.77) -> List[Dict]:
        """
        Select top N picks with diversity constraints
        
        Args:
            predictions: List of prediction dictionaries
            n: Number of picks to return
            require_distinct: Require distinct stat types
            min_gap: Minimum confidence gap for duplicate stats
            min_probability: Minimum probability threshold (default 0.77 = 77%)
            
        Returns:
            List of top N predictions
        """
        if not predictions:
            return []
        
        # Filter by minimum probability first
        filtered = [p for p in predictions if p['probability'] >= min_probability]
        
        if not filtered:
            return []
        
        # Sort by probability (descending)
        sorted_preds = sorted(filtered, key=lambda x: x['probability'], reverse=True)
        
        selected = []
        used_stats = set()
        
        for pred in sorted_preds:
            if len(selected) >= n:
                break
            
            stat = pred['stat']
            
            # Check diversity constraint
            if require_distinct and stat in used_stats:
                # Only allow duplicate stat if significantly different probability
                last_same_stat = next((p for p in selected if p['stat'] == stat), None)
                if last_same_stat:
                    prob_gap = abs(pred['probability'] - last_same_stat['probability'])
                    if prob_gap < min_gap:
                        continue  # Skip this duplicate
            
            selected.append(pred)
            used_stats.add(stat)
        
        return selected
    
    def generate_team_picks(self, team_abbr: str, opponent_abbr: str, date_utc: datetime,
                          preset: str = 'default', alpha: float = 0.85, 
                          min_samples: int = 2, season: int = 2024,
                          use_opponent_filter: bool = True) -> List[Dict]:
        """
        Generate top 5 picks for a team
        
        Args:
            team_abbr: Team abbreviation
            opponent_abbr: Opponent team abbreviation
            date_utc: Target date
            preset: Market preset
            alpha: Recency weight
            min_samples: Minimum sample size
            season: Season year
            use_opponent_filter: Whether to filter by opponent
            
        Returns:
            List of 5 predictions for the team
        """
        # Get player pool for the team
        # Note: This is a simplified version - in production you'd need team roster
        players = self.select_player_pool(team_abbr, date_utc, k=8, season=season)
        
        # If we can't get players from roster, we'd need alternative approach
        # For now, return empty list
        if not players:
            return []
        
        all_predictions = []
        
        for player in players:
            # Build candidate markets
            markets = self.build_candidate_markets(player, preset)
            
            for stat, threshold in markets:
                # Predict probability
                prediction = self.predict_probability(
                    player, stat, threshold, 
                    opponent_abbr if use_opponent_filter else None,
                    date_utc, alpha, season
                )
                
                if prediction and prediction['n_games'] >= min_samples:
                    all_predictions.append(prediction)
        
        # Select top 5 with diversity and minimum 77% probability
        diversity_config = self.config['diversity']
        top_5 = self.top_picks(
            all_predictions, 
            n=5,
            require_distinct=diversity_config.get('require_distinct_stats', True),
            min_gap=diversity_config.get('min_conf_gap_for_duplicate_stat', 0.05),
            min_probability=0.77  # Only show picks with ≥77% probability
        )
        
        return top_5
    
    def generate_game_picks(self, game: Dict, preset: str = 'default', 
                           alpha: float = 0.85, min_samples: int = 2,
                           season: int = 2024, use_opponent_filter: bool = True) -> Dict:
        """
        Generate picks for both teams in a game
        
        Args:
            game: Game dictionary from schedule
            preset: Market preset
            alpha: Recency weight
            min_samples: Minimum sample size
            season: Season year
            use_opponent_filter: Whether to filter by opponent
            
        Returns:
            Dictionary with 'away' and 'home' picks
        """
        away_team = game['visitor_abbr']
        home_team = game['home_abbr']
        date_utc = pd.to_datetime(game['utc_date'])
        
        away_picks = self.generate_team_picks(
            away_team, home_team, date_utc, preset, alpha, min_samples, season, use_opponent_filter
        )
        
        home_picks = self.generate_team_picks(
            home_team, away_team, date_utc, preset, alpha, min_samples, season, use_opponent_filter
        )
        
        return {
            'game_info': game,
            'away_team': away_team,
            'home_team': home_team,
            'away_picks': away_picks,
            'home_picks': home_picks
        }


# Helper functions for export
def export_picks_csv(game_picks: List[Dict]) -> str:
    """Export picks to CSV format"""
    rows = []
    
    for game_pick in game_picks:
        game_info = game_pick['game_info']
        
        for team_type in ['away', 'home']:
            picks = game_pick[f'{team_type}_picks']
            team_abbr = game_pick[f'{team_type}_team']
            
            for pick in picks:
                row = {
                    'date_utc': game_info['utc_date'],
                    'game_id': game_info['gid'],
                    'away_abbr': game_info['visitor_abbr'],
                    'home_abbr': game_info['home_abbr'],
                    'team': team_abbr,
                    'player': pick['player_name'],
                    'market': pick['stat'],
                    'threshold': pick['threshold'],
                    'prob': pick['probability'],
                    'n_games': pick['n_games'],
                    'std': pick['std'],
                    'alpha': pick['alpha'],
                    'badges': ', '.join(pick['badges']),
                    'rationale': pick['rationale']
                }
                rows.append(row)
    
    if not rows:
        return ""
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def export_picks_json(game_picks: List[Dict]) -> str:
    """Export picks to JSON format"""
    import json
    return json.dumps(game_picks, indent=2, default=str)

