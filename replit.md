# NBA Player Performance Predictor

## Overview

The NBA Player Performance Predictor is a data-driven Streamlit application that analyzes NBA player statistics using regression-to-mean modeling and inverse-frequency probability analysis. The application fetches real-time player data from the balldontlie.io API and provides statistical insights into player performance trends, cool-off probabilities, and comparative analysis between players.

The system uses statistical modeling to estimate the likelihood of players maintaining hot streaks versus regressing toward their mean performance levels, with adjustments for career phase, seasonal trends, and recency bias.

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