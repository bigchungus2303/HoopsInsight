# NBA Player Performance Predictor

## Overview

The NBA Player Performance Predictor is a data-driven Streamlit application that analyzes NBA player statistics using regression-to-mean modeling and inverse-frequency probability analysis. The application fetches real-time player data from the balldontlie.io API and provides statistical insights into player performance trends, cool-off probabilities, and comparative analysis between players.

The system uses statistical modeling to estimate the likelihood of players maintaining hot streaks versus regressing toward their mean performance levels, with adjustments for career phase, seasonal trends, and recency bias.

## Recent Changes

### October 2025
- **Playoff vs Regular Season Analysis**: Added season type toggle to analyze playoff and regular season data separately
  - UI toggle between "Regular Season" and "Playoffs" in all player selectors
  - Separate cache entries for regular season (postseason=0) and playoffs (postseason=1)
  - Database migration: Rebuilt season_stats table with UNIQUE(player_id, season, postseason) constraint
  - Playoff averages calculated from individual games (API's season_averages doesn't support postseason)
  - Fixed minutes parsing: Converts "MM:SS" format to decimal for both season types
  - Season headers show type (e.g., "2023-2024 Regular Season" or "2023-2024 Playoffs")
  - DNP filtering applied to both regular season and playoff data

- **Career Phase Decay Toggle**: Added advanced feature to enable career phase weighting in predictions
  - Toggle in Advanced Settings: "Enable Career Phase Decay"
  - Auto-detects career phase: early (🌱), rising (📈), peak (⭐), late (🌅), unknown (❓)
  - Applies lambda decay parameters when enabled (λ early/peak/late)
  - Uses comprehensive regression model with fatigue, minutes, and non-stationarity adjustments
  - Shows career phase indicator when enabled: "[emoji] Career Phase: [Phase]"
  - Lambda sliders disabled when toggle OFF to prevent confusion

- **Next Game Predictions Feature**: Added prediction section showing success probabilities for custom thresholds
  - Displays probability of achieving each threshold in next game (e.g., "≥ 20 points: 65%")
  - Uses weighted frequency from inverse-frequency model with Bayesian smoothing for small samples
  - Shows confidence levels (High if achieved 5+ times, Low otherwise)
  - Configurable thresholds from Advanced Settings (pts, reb, ast, fg3m)
  - Includes expandable info guide explaining probability calculations
  - When career phase enabled, uses career-weighted frequencies instead

- **Season Display Format Update**: Changed all season displays from single year (e.g., "2024") to NBA convention format (e.g., "2024-2025") to better represent that seasons span two calendar years
  - Updated main season selector, favorites selector, and comparison selector
  - Season Statistics header now shows full season format
  - API continues to use base year for requests (e.g., "2024-2025" → API request with year=2024)
  
- **Minutes Field Parser**: Fixed critical bug where minutes per game displayed as 0.0
  - API returns minutes in "MM:SS" string format (e.g., "34:08" for 34 minutes 8 seconds)
  - Added `parse_minutes()` function to convert MM:SS format to decimal (34.08 → 34.13 minutes)
  - Applied parsing to display metrics, z-score calculations, and chart plotting
  - Updated `statistics.py` to handle MM:SS format during z-score normalization
  
- **Full Season Data Availability**: Confirmed 2024-2025 season data available from October 2024 through April 2025
  - Request `per_page=100` to fetch complete season data before sorting
  - Recent games charts now correctly display 2025 dates (March-April 2025)
  - All numeric conversions applied with `pd.to_numeric()` and `safe_float()`

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with session state management
- **Visualization**: Plotly for interactive charts (line charts, bar charts, probability curves)
- **Layout**: Wide layout with expandable sidebar for player search and favorites
- **State Management**: Streamlit session state for selected players, comparison data, and cached visualizations

### Backend Architecture
- **API Client Layer** (`nba_api.py`): Handles communication with balldontlie.io API with retry logic, exponential backoff for rate limiting, and request session management
- **Statistics Engine** (`statistics.py`): Performs z-score normalization, league average calculations, and statistical comparisons
- **Probability Model** (`models.py`): Implements inverse-frequency probability calculations with recency weighting and regression-to-mean analysis using scipy
- **Export Utilities** (`export_utils.py`): Provides CSV and JSON export functionality for player stats, probability analysis, and comparison data

### Data Storage Solutions
- **SQLite Database** (`database.py`): Local caching layer to reduce API calls
  - **Players table**: Stores player biographical data (name, team, position, physical stats)
  - **Season stats table**: Caches season-level performance metrics (PPG, RPG, APG, shooting percentages)
  - Context manager pattern for connection management
  - Timestamp-based cache invalidation
  - Favorites system for quick player access

### Core Statistical Models
- **Inverse-Frequency Probability Model**: Calculates cool-off probabilities using P_inv(x) = 1 - f(x) formula
- **Recency Weighting**: Applies exponential decay to historical data (alpha parameter for weighting recent games)
- **Z-Score Normalization**: Normalizes player stats against league averages for fair comparison
- **Career Phase Adjustment**: Weights historical data based on player career stage (early/peak/late)

### Authentication & Authorization
- **API Key Management**: Uses environment variable `NBA_API_KEY` for balldontlie.io authentication
- **Bearer Token**: Implements Authorization header with Bearer token pattern
- No user authentication layer (single-user desktop application)

## External Dependencies

### Third-Party APIs
- **balldontlie.io API** (v1): Primary data source for NBA player information, season statistics, and game-by-game performance data
  - Rate limiting handled with exponential backoff
  - Endpoints: player search, season stats, game logs
  - Authentication via API key in environment variables

### Python Libraries
- **streamlit**: Web application framework
- **pandas & numpy**: Data manipulation and numerical computations
- **plotly**: Interactive visualization (express and graph_objects modules)
- **scipy**: Statistical functions (stats module for distributions, beta distributions)
- **requests**: HTTP client for API communication
- **sqlite3**: Built-in database engine for caching

### Data Format Dependencies
- **JSON**: API response format and export format
- **CSV**: Export format for statistics and analysis results
- **SQLite**: Local database format for caching

### Environment Configuration
- Requires `NBA_API_KEY` environment variable for API access
- Database file path configurable (defaults to `nba_cache.db`)
- No external configuration files required