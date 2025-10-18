"""
Configuration file for NBA Player Performance Predictor
Contains all constants, defaults, and configuration parameters
"""

# API Configuration
API_BASE_URL = "https://api.balldontlie.io/v1"
API_TIMEOUT = 10
API_MAX_RETRIES = 3
API_RATE_LIMIT_BACKOFF_BASE = 2  # Exponential backoff base

# Database Configuration
DATABASE_PATH = "nba_cache.db"
CACHE_EXPIRY_DAYS = 7
PLAYER_CACHE_DAYS = 7
SEASON_CACHE_DAYS = 1
GAME_CACHE_DAYS = 1
LEAGUE_AVG_CACHE_DAYS = 7

# Statistical Model Defaults
DEFAULT_ALPHA = 0.85  # Recency weighting factor
DEFAULT_WINDOW_SIZE = 10  # Window for rolling calculations
DEFAULT_LOOKBACK_WINDOW = 20  # Window for non-stationarity detection

# Career Phase Lambda Parameters
LAMBDA_EARLY = 0.02
LAMBDA_RISING = 0.03
LAMBDA_PEAK = 0.05
LAMBDA_LATE = 0.08
LAMBDA_UNKNOWN = 0.04

# Threshold Configurations
DEFAULT_THRESHOLDS = {
    'pts': [10, 15, 20, 25, 30],
    'reb': [4, 6, 8, 10, 12],
    'ast': [4, 6, 8, 10, 12],
    'fg3m': [2, 3, 4, 5]
}

# Coefficient of Variation Estimates for Dynamic Thresholds
CV_ESTIMATES = {
    'pts': 0.35,  # Points typically have ~35% CV
    'reb': 0.40,  # Rebounds ~40% CV
    'ast': 0.50   # Assists ~50% CV (more variable)
}

# League Average Defaults (2024 season approximation)
DEFAULT_LEAGUE_AVERAGES = {
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

# Season Configuration
AVAILABLE_SEASONS = list(range(2024, 2019, -1))  # [2024, 2023, 2022, 2021, 2020]
CURRENT_SEASON_DEFAULT = 2024

# UI Configuration
APP_TITLE = "NBA Player Performance Predictor"
APP_ICON = "🏀"
PAGE_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Recent Games Configuration
RECENT_GAMES_DEFAULT_LIMIT = 20
RECENT_GAMES_MIN_FOR_CACHE = 5
RECENT_GAMES_CHART_DISPLAY = 10

# Bayesian Smoothing Configuration
BAYESIAN_PRIOR_ALPHA = 2.0  # Mildly informative prior
BAYESIAN_PRIOR_BETA = 2.0
BAYESIAN_SMALL_SAMPLE_THRESHOLD = 10  # Apply Bayesian smoothing below this

# Statistical Significance
CONFIDENCE_LEVEL = 0.95
P_VALUE_THRESHOLD = 0.05
HIGH_CONFIDENCE_MIN_EXCEEDS = 5  # Minimum times threshold exceeded for "high confidence"

# Fatigue Analysis
FATIGUE_WINDOW_SIZE = 10
FATIGUE_REGRESSION_THRESHOLD = 1.0  # Z-score threshold for regression risk
FATIGUE_MULTIPLIER_MAX = 0.3  # Maximum adjustment from fatigue

# Minutes Trend Analysis
MINUTES_TREND_WINDOW = 10
MINUTES_DECLINING_SLOPE_THRESHOLD = -0.5
MINUTES_TREND_P_VALUE = 0.1
MINUTES_SUSTAINABILITY_MIN = 0.3

# Non-Stationarity Detection
REGIME_CHANGE_Z_THRESHOLD = 1.5
REGIME_CHANGE_ADJUSTMENT_FACTOR = 0.7

# Export Configuration
EXPORT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Visualization Colors
CHART_COLORS = {
    'pts': '#1f77b4',
    'reb': '#ff7f0e',
    'ast': '#2ca02c',
    'fg3m': '#d62728',
    'min': '#9467bd'
}

# Career Phase Emojis
CAREER_PHASE_EMOJIS = {
    "early": "🌱",
    "rising": "📈",
    "peak": "⭐",
    "late": "🌅",
    "unknown": "❓"
}

# Player Filtering
MIN_GAMES_FOR_LEAGUE_AVG = 20  # Minimum games played to include in league average calculation
MIN_MINUTES_FOR_PLAYED_GAME = 0  # Minimum minutes to consider a game "played"

# API Pagination
DEFAULT_PER_PAGE = 100
MAX_PER_PAGE = 100

