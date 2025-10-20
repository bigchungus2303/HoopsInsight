# NBA Performance Predictor 🏀

A sophisticated NBA player performance analysis and prediction tool using regression-to-mean analysis with inverse-frequency probability modeling.

## Features

### **Three Powerful Pages:**

#### **1. Player Analysis** (Predictive)
- **Player Search**: Find NBA players with autocomplete functionality
- **Season Statistics**: View per-game averages and shooting percentages
- **Season Performance Analysis**: Analyze all games from selected season (up to 100 games)
- **Opponent-Specific Analysis**: Filter predictions by opponent team with autocomplete search
  - Loads ALL games vs specific opponent from selected season
  - Provides sample size warnings for reliability
- **Inverse-Frequency Model**: Calculate regression-to-mean probabilities
- **AI Lambda Advisor**: Auto-optimize career phase decay parameters
- **Career Phase Weighting**: Adjust for early/peak/late career phases
- **Player Comparison**: Side-by-side statistical analysis
- **Minutes Trend Analysis**: Track playing time patterns and sustainability
- **Save Predictions**: Track predictions for model validation

#### **2. Season Report** (Descriptive)
- **Independent Player Search**: Load players directly in this page
- **Custom Date Filtering**: Analyze by month or custom date range
- **Descriptive Statistics**: Mean, median, std dev, min, max (PTS, REB, AST, 3PM, MIN)
- **Performance Trends**: 4 line charts tracking Points, Rebounds, Assists, 3-Pointers
- **Monthly Comparison**: Compare performance across months (includes 3-point stats)
- **Game Log**: Complete game-by-game breakdown with all stats
- **Anomaly Detection**: Auto-detect DNPs, low minutes, statistical outliers (including 3PM)

#### **3. Prediction History** (Validation)
- **Track Predictions**: Save and verify predictions after games
- **Accuracy Metrics**: Overall and per-category accuracy rates
- **Verification Interface**: Simple input for actual game results
- **Model Performance**: Monitor prediction accuracy over time

### **Advanced Features:**
- **Custom Thresholds**: Set single target threshold for each stat category
- **API Usage Dashboard**: Real-time cache performance monitoring
- **Visual Confidence Meters**: Easy-to-read prediction reliability
- **Export Functionality**: Export data as CSV or JSON

## Quick Start

### Prerequisites

- Python 3.7 or higher
- Virtual environment (included as `env/`)

### Installation

1. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Option 1: Using the Batch File (Easiest)
Double-click `run_app.bat` or run in command prompt:
```bash
run_app.bat
```

#### Option 2: Manual Command
Activate the virtual environment and run:
```bash
# Activate virtual environment
env\Scripts\activate

# Run the app
streamlit run app.py
```

#### Option 3: Direct Command
```bash
.\env\Scripts\python.exe -m streamlit run app.py
```

The app will start and automatically open in your browser at:
**http://localhost:8501**

## Project Structure

```
HoopsInsight/
├── app.py                   # Main Streamlit application (entry point)
├── launch.py                # Cross-platform launcher script
├── run_app.bat              # Windows quick launch script
├── run_tests.py             # Test runner
│
├── Core Modules/
│   ├── nba_api.py          # NBA API client with caching
│   ├── database.py         # SQLite database operations
│   ├── models.py           # Statistical models (Inverse-Frequency, Bayesian)
│   ├── statistics.py       # Statistical calculations and analysis
│   ├── config.py           # Configuration and constants
│   ├── logger.py           # Logging setup
│   ├── error_handler.py    # Error handling utilities
│   └── export_utils.py     # Data export functions (CSV/JSON)
│
├── components/              # Reusable UI components
│   ├── __init__.py
│   ├── api_dashboard.py    # API usage & cache statistics
│   ├── advanced_settings.py # Threshold sliders & settings
│   ├── prediction_cards.py # Prediction display widgets
│   ├── charts.py           # Reusable Plotly charts
│   └── lambda_advisor.py   # AI-powered lambda recommendations
│
├── pages/                   # Application pages
│   ├── __init__.py
│   ├── prediction_history.py  # Prediction tracking & accuracy
│   └── season_report.py    # Descriptive statistical analysis
│
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── README.md
│   ├── test_models.py
│   ├── test_statistics.py
│   └── test_error_handling.py
│
├── docs/                    # Documentation
│   ├── IMPROVEMENTS.md      # Feature changelog
│   ├── TESTING.md           # Testing guide
│   ├── DATABASE_ARCHITECTURE.md  # Database documentation
│   ├── DATABASE_DIAGRAM.md  # Visual DB structure
│   ├── REFACTORING_SUMMARY.md   # Code refactoring notes
│   ├── PREDICTION_HISTORY_SUMMARY.md
│   ├── SEASON_REPORT_SUMMARY.md
│   ├── LAMBDA_ADVISOR_UI.md
│   ├── SEASON_REPORT_INDEPENDENCE.md
│   ├── FIXES_APPLIED.md
│   └── TROUBLESHOOTING_PAGES.md
│
├── attached_assets/         # Project assets
│   ├── nba-stats-mvp.md    # Project specification
│   └── image_*.png         # Screenshots
│
├── .streamlit/
│   └── config.toml         # Streamlit configuration
│
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
└── nba_cache.db            # SQLite cache (gitignored)
```

## Configuration

### Environment Variables (Optional)
- `NBA_API_KEY`: API key for balldontlie.io (optional, but recommended to avoid rate limiting)

### Streamlit Configuration
Edit `.streamlit/config.toml` to customize:
- Server port (default: 8501)
- Theme settings
- Headless mode

## Usage

1. **Search for a Player**: Use the sidebar to search for NBA players
2. **Select Season**: Choose the season and type (Regular Season/Playoffs)
3. **View Analysis**: 
   - Season statistics and shooting percentages
   - Recent game performance trends
   - Probability predictions for next game
   - Minutes played trend analysis
4. **Compare Players**: Search for a second player to compare side-by-side
5. **Export Data**: Download analysis results as CSV or JSON

## Advanced Settings

Access advanced settings from the sidebar to customize:
- **Custom Thresholds**: Set single target threshold for each stat (Points, Rebounds, Assists, 3PM)
- **Recency Weight (α)**: Adjust how much weight to give recent games
- **Career Phase Decay**: Enable/disable career phase adjustments

## Data Source

All NBA data is sourced from [balldontlie.io](https://balldontlie.io) API.

## Technologies

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Plotly**: Interactive visualizations
- **SciPy**: Statistical functions
- **Requests**: HTTP API calls

## Troubleshooting

### App won't start
- Make sure the virtual environment is activated
- Check that all packages are installed: `pip list`
- Try running directly: `.\env\Scripts\python.exe -m streamlit run app.py`

### Port already in use
- Edit `.streamlit/config.toml` and change the port number
- Or kill the process using the port

### Import errors
- Reinstall dependencies: `pip install -r requirements.txt`
- Make sure you're using Python 3.7+

## 📚 Documentation

### **Core Documents:**

| Document | Purpose | Audience |
|----------|---------|----------|
| **README.md** (this file) | Getting started, features, usage | Users |
| **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** | Architecture, API, database, testing | Developers |
| **[CHANGELOG.md](CHANGELOG.md)** | Feature history, updates | Everyone |
| **[nba-stats-mvp.md](attached_assets/nba-stats-mvp.md)** | Mathematical spec, formulas | Developers |
| **[tests/README.md](tests/README.md)** | Testing guide | Developers |

### **Quick Links:**
- 🆕 **What's new?** → Read [CHANGELOG.md](CHANGELOG.md)
- 🔧 **How to develop?** → Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- 🧪 **How to test?** → Read [tests/README.md](tests/README.md)
- 📊 **Model details?** → Read [nba-stats-mvp.md](attached_assets/nba-stats-mvp.md)

---

## License

Apache License 2.0

## Contributing

This project uses:
- Inverse-Frequency Probability Model for predictions
- Bayesian smoothing for small sample sizes
- Career phase decay parameters for aging adjustments
- Minutes trend analysis for playing time sustainability

**Before contributing:**
1. Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
2. Check [nba-stats-mvp.md](attached_assets/nba-stats-mvp.md) for model spec
3. Run tests: `python run_tests.py`

---

**Built with ❤️ for NBA analytics enthusiasts**


