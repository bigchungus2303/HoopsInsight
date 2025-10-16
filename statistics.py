import pandas as pd
import numpy as np
from typing import Dict, List
from scipy import stats

class StatisticsEngine:
    """Engine for statistical calculations and normalizations"""
    
    def __init__(self):
        self.league_cache = {}
    
    def get_league_averages(self, season: int) -> Dict:
        """Get or calculate league averages for a season"""
        if season in self.league_cache:
            return self.league_cache[season]
        
        # Default NBA league averages (approximate for 2024 season)
        league_averages = {
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
        
        self.league_cache[season] = league_averages
        return league_averages
    
    def calculate_z_scores(self, player_stats: pd.DataFrame, league_averages: Dict) -> pd.DataFrame:
        """Calculate z-scores for player stats relative to league averages"""
        result = player_stats.copy()
        
        stats_to_normalize = ['pts', 'reb', 'ast', 'fg_pct', 'fg3_pct', 'ft_pct', 'min']
        
        for stat in stats_to_normalize:
            if stat in player_stats.columns and f'{stat}_std' in league_averages:
                # Special handling for minutes field which comes in MM:SS format
                if stat == 'min':
                    result[stat] = result[stat].apply(lambda x: self._parse_minutes(x))
                else:
                    # Convert to numeric to handle string values from API
                    result[stat] = pd.to_numeric(result[stat], errors='coerce')
                
                league_mean = league_averages[stat]
                league_std = league_averages[f'{stat}_std']
                
                if league_std > 0:
                    result[f'{stat}_z'] = (result[stat] - league_mean) / league_std
                else:
                    result[f'{stat}_z'] = 0.0
        
        return result
    
    def _parse_minutes(self, min_value):
        """Parse minutes from MM:SS format to decimal"""
        if not min_value:
            return 0.0
        try:
            # If already a number, return it
            return float(min_value)
        except (ValueError, TypeError):
            pass
        try:
            # Parse MM:SS format
            if isinstance(min_value, str) and ':' in min_value:
                parts = min_value.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes + (seconds / 60.0)
            return 0.0
        except:
            return 0.0
    
    def calculate_dynamic_thresholds(self, season_stats: Dict) -> Dict:
        """Calculate dynamic thresholds based on player's mean and std deviation"""
        thresholds = {}
        
        # For this implementation, we'll use the season stats as the mean
        # and estimate std deviation based on typical NBA variance patterns
        
        stats_to_analyze = ['pts', 'reb', 'ast']
        
        # Typical coefficient of variation for NBA stats
        cv_estimates = {
            'pts': 0.35,    # Points typically have ~35% CV
            'reb': 0.40,    # Rebounds ~40% CV
            'ast': 0.50     # Assists ~50% CV (more variable)
        }
        
        for stat in stats_to_analyze:
            if stat in season_stats and season_stats[stat] is not None:
                mean_val = season_stats[stat]
                
                # Estimate standard deviation using coefficient of variation
                std_val = mean_val * cv_estimates.get(stat, 0.35)
                
                thresholds[stat] = {
                    'mean': mean_val,
                    'std': std_val,
                    'plus_1_std': mean_val + std_val,
                    'plus_2_std': mean_val + 2 * std_val,
                    'plus_3_std': mean_val + 3 * std_val
                }
        
        return thresholds
    
    def calculate_career_phase(self, career_stats: List[Dict]) -> str:
        """Determine career phase based on statistical trends"""
        if not career_stats or len(career_stats) < 2:
            return "unknown"
        
        # Sort by season
        career_sorted = sorted(career_stats, key=lambda x: x.get('season', 0))
        
        # Extract points per game over time
        pts_trend = [s.get('pts', 0) for s in career_sorted if s.get('pts') is not None]
        
        if len(pts_trend) < 3:
            return "early"
        
        # Calculate trend using linear regression
        x = np.arange(len(pts_trend))
        slope, _, r_value, _, _ = stats.linregress(x, pts_trend)
        
        # Determine career phase based on trend and career length
        career_length = len(pts_trend)
        
        if career_length <= 3:
            return "early"
        elif career_length >= 10 and slope < -0.5:
            return "late"
        elif slope > 0.5:
            return "rising"
        else:
            return "peak"
    
    def calculate_career_phase_weights(self, career_phase: str, num_games: int, lambda_params: dict = None) -> np.ndarray:
        """Calculate exponential decay weights based on career phase"""
        
        # Lambda values for different career phases
        if lambda_params:
            lambda_values = {
                "early": lambda_params.get('early', 0.02),
                "rising": lambda_params.get('early', 0.02),
                "peak": lambda_params.get('peak', 0.05),
                "late": lambda_params.get('late', 0.08),
                "unknown": lambda_params.get('peak', 0.05)
            }
        else:
            lambda_values = {
                "early": 0.02,    # Less decay - recent performance more indicative
                "rising": 0.03,   # Moderate decay
                "peak": 0.05,     # Balanced weighting
                "late": 0.08,     # More decay - regression more likely
                "unknown": 0.04   # Default moderate decay
            }
        
        lambda_val = lambda_values.get(career_phase, 0.04)
        
        # Create exponential decay weights
        # w_i = e^(-λ(T-t_i)) where T is total games, t_i is game index
        weights = np.array([np.exp(-lambda_val * (num_games - i - 1)) for i in range(num_games)])
        
        # Normalize weights to sum to 1
        weights = weights / weights.sum()
        
        return weights
    
    def calculate_seasonal_normalization(self, games_data: pd.DataFrame, season_average: float) -> pd.DataFrame:
        """Apply seasonal normalization to game data"""
        result = games_data.copy()
        
        stats_to_normalize = ['pts', 'reb', 'ast', 'fg3m']
        
        for stat in stats_to_normalize:
            if stat in games_data.columns:
                # Calculate z-scores relative to season average
                if stat in ['pts', 'reb', 'ast']:
                    # Use season average as mean, estimate std
                    season_mean = season_average
                    season_std = season_mean * 0.35  # Typical CV
                else:
                    # For other stats, use data-driven approach
                    season_mean = games_data[stat].mean()
                    season_std = games_data[stat].std()
                
                if season_std > 0:
                    result[f'{stat}_zscore'] = (games_data[stat] - season_mean) / season_std
                else:
                    result[f'{stat}_zscore'] = 0.0
        
        return result
    
    def detect_outliers(self, data: List[float], method: str = 'iqr') -> List[bool]:
        """Detect outliers in performance data"""
        if not data or len(data) < 4:
            return [False] * len(data)
        
        data_array = np.array(data)
        
        if method == 'iqr':
            Q1 = np.percentile(data_array, 25)
            Q3 = np.percentile(data_array, 75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = (data_array < lower_bound) | (data_array > upper_bound)
        
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(data_array))
            outliers = z_scores > 2.5
        
        else:  # Modified z-score
            median = np.median(data_array)
            mad = np.median(np.abs(data_array - median))
            modified_z_scores = 0.6745 * (data_array - median) / mad
            outliers = np.abs(modified_z_scores) > 3.5
        
        return outliers.tolist()
    
    def calculate_consistency_metrics(self, games_data: pd.DataFrame) -> Dict:
        """Calculate various consistency metrics for player performance"""
        metrics = {}
        
        stats_to_analyze = ['pts', 'reb', 'ast']
        
        for stat in stats_to_analyze:
            if stat in games_data.columns:
                values = games_data[stat].dropna()
                
                if len(values) > 0:
                    metrics[f'{stat}_mean'] = values.mean()
                    metrics[f'{stat}_std'] = values.std()
                    metrics[f'{stat}_cv'] = values.std() / values.mean() if values.mean() > 0 else 0
                    metrics[f'{stat}_median'] = values.median()
                    metrics[f'{stat}_range'] = values.max() - values.min()
                    
                    # Calculate consistency score (inverse of coefficient of variation)
                    cv = metrics[f'{stat}_cv']
                    metrics[f'{stat}_consistency'] = 1 / (1 + cv) if cv > 0 else 1.0
        
        return metrics
    
    def calculate_momentum(self, recent_values: List[float], window_size: int = 5) -> Dict:
        """Calculate momentum indicators for recent performance"""
        if len(recent_values) < window_size:
            return {'trend': 'insufficient_data', 'momentum_score': 0.0}
        
        values = np.array(recent_values[-window_size:])
        
        # Calculate trend using linear regression
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Momentum score based on slope and correlation
        momentum_score = slope * abs(r_value) if p_value < 0.05 else 0.0
        
        # Classify trend
        if abs(slope) < 0.1:
            trend = 'stable'
        elif slope > 0.1:
            trend = 'improving'
        else:
            trend = 'declining'
        
        return {
            'trend': trend,
            'momentum_score': momentum_score,
            'slope': slope,
            'correlation': r_value,
            'p_value': p_value
        }
