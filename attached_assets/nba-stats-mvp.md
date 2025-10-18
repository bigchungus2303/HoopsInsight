# NBA Player Performance Predictor – Project Specification & Execution Plan

## 🎯 Purpose
A data-driven application that fetches NBA player statistics and models **regression-to-mean** behavior using both descriptive statistics and probabilistic analysis.  
The goal is to estimate the **cool-off probability** (inverse-likelihood of repeating high performances) across points, assists, rebounds, and 3-pointers — adjusted for player career phase, seasonal normalization, and fatigue/load effects.

---

## 🧱 Core Functional Modules

### 1. Player Search
- Autocomplete search using `balldontlie.io` API  
- Display: **Name**, **Team**, **Position**, **Height**, **Weight**  
- On select:
  - Fetch season averages  
  - Fetch last 5 games  
  - Load career data for weighting model

### 2. Season Statistics
Displays per-game season metrics:
- **PPG**, **RPG**, **APG**, **FG%**, **3P%**, **FT%**, **MPG**, **Minutes Played**
- Includes z-score normalization against league averages

### 3. Player Comparison
- Dual-player comparison layout  
- Interactive bar charts for **PTS**, **REB**, **AST**, **FG%**, **3P%**  
- Overlay of inverse-likelihood “cool-off” probability curves

### 4. Recent Game Performance
- Line chart for last 5 games showing **points**, **rebounds**, **assists**, and **minutes played**  
- Tooltips with detailed game stats  
- Dynamic updates on player/season change

### 5. Inverse-Frequency Probability Model

**Core Formula:**
\[
P_{inv}(x) = 1 - f(x), \quad f(x) = \frac{1}{N}\sum I[\text{stat}_i ≥ t]
\]

**Adjustments:**
1. **Career Phase Weighting**
   - Early → rising trend (recent seasons weighted higher)  
   - Peak → stable mean (balanced weighting)  
   - Late → decline (stronger exponential decay)  
   \[
   w_i = e^{-λ (T - t_i)}
   \]

2. **Seasonal Normalization (z-score)**
   \[
   z = \frac{x - μ_{season}}{σ_{season}}
   \]

3. **Dynamic Player Thresholds**
   \[
   \text{thresholds} = \{μ, μ+σ, μ+2σ, μ+3σ\}
   \]

4. **Fatigue / Load Curve**
   - Rolling 10-game mean vs long-term mean  
   - If current > mean +1σ → regression likelihood ↑

5. **Injury / Minutes-Played Filter**
   - Declining minutes = lower sustain probability

6. **Non-Stationarity Handling**
   - Recency weighting keeps responsiveness while retaining long-term variance

---

## 📊 Statistical Thresholds
| Category | Thresholds |
|-----------|-------------|
| Points | 10, 15, 20 |
| Rebounds | 4, 6, 8, 10 |
| Assists | 4, 6, 8, 10 |
| 3-Pointers | 2, 3, 5 |

Each threshold:
- Computes **frequency**, **inverse-likelihood**, and **weighted inverse-likelihood**
- Visualized in grouped bar charts per stat

---

## 📈 Visualization
1. **Frequency vs Inverse-Likelihood Bar Charts** – For PTS, REB, AST, 3PM  
2. **Career-Adjusted Cool-Off Curve** – Regression probability by player phase  
3. **Dual Comparison Dashboard** – Side-by-side player view  
4. **Fatigue Curve** – Rolling vs historical mean (minutes & output)

---

## ⚙️ Tech Stack
| Layer | Technology |
|--------|-------------|
| **Frontend** | Streamlit (Production) |
| **Backend** | Direct API Integration |
| **Data Source** | `balldontlie.io` API v1 |
| **Computation Engine** | NumPy / Pandas / SciPy |
| **Visualization** | Plotly (express & graph_objects) |
| **Persistence** | SQLite (caching + favorites) |
| **Python Version** | 3.11+ (Recommended) |

---

## 🧮 Data Model

### Player
| Field | Type | Description |
|--------|------|-------------|
| id | int | Player ID |
| name | string | Full name |
| team | string | Team |
| position | string | Role |
| height / weight | string | Physical data |

### Season Stats
| Field | Type |
|--------|------|
| pts | float |
| reb | float |
| ast | float |
| fg_pct | float |
| fg3_pct | float |
| ft_pct | float |
| min | float |
| games_played | int |

### Game Record
| Field | Type |
|--------|------|
| date | string |
| pts, reb, ast, fg3m | float |
| min | float |
| season | int |

---

# 🧭 Execution Plan

## Step 1: Repository Bootstrap
```bash
# Clone or navigate to project
cd HoopsInsight

# Create virtual environment (Python 3.11+ recommended)
python -m venv env

# Activate virtual environment
# Windows PowerShell:
.\env\Scripts\Activate.ps1
# Windows CMD:
env\Scripts\activate.bat
# Linux/Mac:
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Requirements (Python 3.11+):**
```txt
streamlit>=1.23.0
pandas>=1.5.0
numpy>=1.23.0
plotly>=5.14.0
requests>=2.28.0
scipy>=1.10.0
```

## Step 2: Data Layer
Create:
- `fetch_nba.py` → API client with retry & pagination  
- `analyze.py` → inverse-likelihood model  
- `data/` → JSON/CSV storage

Example:
```bash
python fetch_nba.py --player "LeBron James" --season 2024 --last 5 --out json,csv
python analyze.py --file data/lebron_james_*.json --targets "pts:10,15,20;ast:5,8,10"
```

## Step 3: CLI Validation
- Check outputs  
- Validate JSON & CSV content  
- Tune α (recency weight) between 0.8–0.9

## Step 4: Streamlit / Web UI
- Streamlit MVP  
- Interactive stats & charts  
- Expand later into React + FastAPI

---

## 📂 Directory Structure (Clean & Organized)
```
HoopsInsight/
├── app.py                    # Main Streamlit application
├── launch.py                 # Cross-platform launcher
├── run_app.bat               # Windows quick launch
├── run_tests.py              # Test runner
│
├── Core Modules/
│   ├── nba_api.py           # NBA API client with caching
│   ├── database.py          # SQLite database operations
│   ├── models.py            # Statistical models (Inverse-Frequency, Bayesian)
│   ├── statistics.py        # Statistical calculations and analysis
│   ├── config.py            # Centralized configuration
│   ├── logger.py            # Logging infrastructure
│   ├── error_handler.py     # Error handling utilities
│   └── export_utils.py      # Data export (CSV/JSON)
│
├── components/               # ✨ Reusable UI components
│   ├── __init__.py
│   ├── api_dashboard.py     # API usage & cache statistics
│   ├── advanced_settings.py # Threshold sliders & settings
│   ├── prediction_cards.py  # Prediction display widgets
│   ├── charts.py            # Reusable Plotly charts
│   └── lambda_advisor.py    # AI lambda recommendations
│
├── pages/                    # ✨ Application pages
│   ├── __init__.py
│   ├── prediction_history.py  # Prediction tracking & accuracy
│   └── season_report.py     # Descriptive statistical analysis
│
├── tests/                    # Unit tests (25+ tests)
│   ├── __init__.py
│   ├── README.md
│   ├── test_models.py
│   ├── test_statistics.py
│   └── test_error_handling.py
│
├── docs/                     # ✨ NEW: Documentation folder
│   ├── IMPROVEMENTS.md       # Feature changelog
│   ├── TESTING.md            # Testing guide
│   ├── PROJECT_STRUCTURE.md  # Structure overview
│   ├── DATABASE_ARCHITECTURE.md  # Database deep dive
│   ├── DATABASE_DIAGRAM.md   # Visual DB diagrams
│   └── [8 more feature docs]
│
├── attached_assets/          # Project assets
│   ├── nba-stats-mvp.md     # This specification
│   └── image_*.png          # Screenshots
│
├── .streamlit/
│   └── config.toml          # Streamlit configuration
│
├── Configuration/
│   ├── .gitignore           # Git exclusions
│   ├── requirements.txt     # Python dependencies
│   └── pyproject.toml       # Project metadata
│
└── nba_cache.db            # SQLite cache (gitignored)
```

**Clean, organized, professional structure!** ✨

---

## 🧠 Modeling Rules
\[
\hat{p}_{\ge t} = \frac{1}{N}\sum I[x_i \ge t], \quad q_{\ge t} = 1 - \hat{p}_{\ge t}
\]
Weighted version:
\[
w_i = α^{N-i}, \quad \hat{p}^{(w)} = \sum w_i I[x_i \ge t], \quad q^{(w)} = 1 - \hat{p}^{(w)}
\]
Career-phase weighting:
\[
w_i = e^{-λ (T - t_i)}, \quad λ_{early} < λ_{peak} < λ_{late}
\]
Z-score normalization:
\[
z = \frac{x - μ_{season}}{σ_{season}}
\]

---

## ✅ Testing Checklist
- Player not found → handled  
- Small N → stable output  
- α = 1 → unweighted results  
- α < 1 → recent games emphasized  
- Output written to `_analysis.json`

---

## 🧪 Notebook
`notebooks/exploration.ipynb`: visualize inverse vs frequency and validate trends.

---

## 🗂 Cursor Rule
```
Always read nba-stats.md before coding.
Document CLI flags, formulas, and assumptions.
Update when model logic or API data structure changes or Update documentation after major features
Frontend only starts after CLI validation.
```

---

## 🧾 Data Contract

### Input JSON
```json
{
  "player": { "id": 15, "first_name": "LeBron", "last_name": "James" },
  "season": 2024,
  "games": [
    { "date": "2024-03-12", "pts": 25, "reb": 7, "ast": 9, "fg3m": 2, "min": 34 }
  ]
}
```

### Output JSON
```json
{
  "player": "LeBron James",
  "season": 2024,
  "n_games": 5,
  "alpha": 0.85,
  "targets": { "pts": [10,15,20], "ast": [5,8,10] },
  "results": {
    "pts": [
      { "threshold": 10, "frequency": 0.8, "inverse": 0.2, "weighted_freq": 0.77, "weighted_inverse": 0.23 }
    ]
  }
}
```

---

## 🧩 Future Enhancements
- Bayesian smoothing for probabilities  
- Multi-season calibration with exponential decay  
- Team-level fatigue and back-to-back adjustments  
- Player similarity clustering (z-score vectors)  
- Next-game stat distribution simulation  

---

## 📌 Backlog Priority
1. ✅ CLI fetch + analysis  
2. ✅ Weighted inverse model  
3. ✅ Streamlit charts  
4. ✅ Career-phase weighting  
5. ✅ Dynamic thresholds (μ + nσ)  
6. ✅ Fatigue/load curve  
7. ✅ Minutes/injury filter  
8. ✅ Player comparison dashboard
9. ✅ Favorites system
10. ✅ Data export (CSV/JSON)
11. ✅ Bayesian smoothing for small samples
12. ✅ Multi-season support (2020-2025)
13. ✅ Playoffs vs Regular Season toggle
14. ✅ Comprehensive error handling & UX improvements
15. ✅ Data quality indicators
16. ✅ Interactive threshold sliders (October 18, 2025) ✨
17. ✅ API rate limit monitoring & cache statistics (October 18, 2025) ✨
18. ✅ Visual confidence meters with progress bars (October 18, 2025) ✨
19. ✅ App.py modularization (October 18, 2025) ✨
20. ✅ Prediction history & model tracking (October 18, 2025) ✨
21. ✅ Lambda auto-advisor with AI recommendations (October 18, 2025) ✨
22. ✅ Season performance report with date filtering (October 18, 2025) ✨
23. ✅ UI simplification - removed academic sections (October 18, 2025) ✨
24. ✅ Simple prediction cards with betting guide (October 18, 2025) ✨
25. ✅ Opponent team tracking in Season Report (October 18, 2025) ✨
26. ✅ Opponent-specific prediction filtering (October 18, 2025) ✨
27. ⏳ Historical multi-season charts (next priority)
28. ⏳ React frontend migration (future enhancement)

## 📝 Implementation Updates (October 2025)

### Interactive Threshold Sliders ✨ NEW (October 18, 2025)
**Major UX Improvement:**
- Replaced comma-separated text inputs with interactive sliders
- **Features:**
  - 4 customizable sliders per stat category (Points, Rebounds, Assists, 3-Pointers)
  - Appropriate min/max ranges for each stat type
  - Visual feedback with tooltips
  - Automatic sorting and duplicate removal
- **Ranges:**
  - Points: 5-50 (default: 10, 15, 20, 25)
  - Rebounds: 1-20 (default: 4, 6, 8, 10)
  - Assists: 1-20 (default: 4, 6, 8, 10)
  - 3-Pointers: 0-15 (default: 2, 3, 5, 7)
- **Impact:** Much more intuitive than text input, real-time visual adjustments

### API Usage Dashboard ✨ NEW (October 18, 2025)
**Performance Monitoring Feature:**
- Real-time API usage statistics in sidebar
- **Metrics Displayed:**
  - API Calls: Actual API requests made
  - Cache Hits: Data retrieved from cache
  - Total Requests: Combined count
  - Cache Hit Rate: Efficiency percentage
- **Visual Indicators:**
  - ✅ Excellent (≥70%) - Green indicator
  - ℹ️ Good (40-69%) - Blue indicator
  - ⚠️ Low (<40%) - Yellow warning
- **Backend:**
  - Added `cache_hit_count` tracking to NBAAPIClient
  - New `get_cache_stats()` method returns comprehensive statistics
- **Impact:** Users can see app performance and cache efficiency at a glance

### Visual Confidence Meters ✨ NEW (October 18, 2025)
**Enhanced Prediction Display:**
- Progress bars showing success probabilities visually
- Color-coded confidence indicators:
  - 🟢 High confidence (≥5 occurrences)
  - 🟡 Low confidence (<5 occurrences)
- Percentage text overlaid on progress bars
- Applied to all prediction categories (Points, Rebounds, Assists, 3-Pointers)
- **Impact:** Users can quickly assess prediction reliability at a glance

### App.py Modularization ✨ NEW (October 18, 2025)
**Major Code Organization Improvement:**
- Refactored monolithic `app.py` (1091 lines) into modular components
- **Size Reduction:** Removed ~234 lines (21% reduction) → now ~857 lines
- **New Structure:**
  - `components/` directory for reusable widgets
  - `pages/` directory (ready for future page modules)

**Components Created:**
1. `components/api_dashboard.py` - API usage statistics display (50 lines)
2. `components/advanced_settings.py` - Threshold sliders & career phase settings (145 lines)
3. `components/prediction_cards.py` - Prediction cards with progress bars (60 lines)
4. `components/charts.py` - Reusable Plotly chart functions (150 lines)

**Benefits:**
- ✅ Better code organization and separation of concerns
- ✅ Easier to maintain (smaller, focused files)
- ✅ Reusable components across the app
- ✅ Easier testing of individual components
- ✅ Foundation for future page-based architecture
- ✅ Improved developer experience

**Technical Details:**
- All components properly import necessary dependencies
- No breaking changes to existing functionality
- Maintains all session state management
- Clean interfaces between components and main app

### Prediction History & Model Tracking ✨ NEW (October 18, 2025)
**Complete Prediction Tracking System:**
- Full end-to-end prediction tracking workflow
- Backend was already complete; added frontend UI

**New Features:**
1. **Prediction History Page:**
   - Accessible via dropdown navigation in top-right
   - Three tabs: Accuracy Metrics, Recent Predictions, Verify Predictions
   - Clean, intuitive interface for tracking model performance

2. **Save Predictions:**
   - Save any prediction from player analysis page
   - Select specific thresholds to track with checkboxes
   - Date picker for scheduling game dates
   - One-click save functionality

3. **Accuracy Metrics Dashboard:**
   - Overall accuracy percentage across all predictions
   - Breakdown by stat category (Points, Rebounds, Assists, 3PM)
   - Visual progress bars for each category
   - Detailed breakdown by threshold ranges

4. **Verification Interface:**
   - Lists all unverified predictions (past game date)
   - Simple number input for actual results
   - Automatic correctness calculation
   - Real-time updates to accuracy metrics

5. **Recent Predictions View:**
   - Filterable list of all saved predictions
   - Filter by verified/unverified status
   - Shows actual results for verified predictions
   - Export-ready data format

**User Workflow:**
1. View player → See predictions → Select predictions to save → Save with game date
2. After game → Switch to Prediction History → Verify with actual results
3. Watch accuracy metrics build up over time
4. Validate model performance

**Technical Implementation:**
- New file: `pages/prediction_history.py` (~230 lines)
- Updated: `app.py` with navigation and save functionality
- Uses existing database methods (no backend changes needed)
- Tab-based interface for clear separation of functions

**Impact:**
- ✅ Enables model validation and performance tracking
- ✅ Provides accountability for predictions
- ✅ Helps users understand model accuracy
- ✅ Foundation for future ML/statistical improvements

### Season Performance Report ✨ NEW (October 18, 2025)
**Complete Descriptive Statistical Analysis:**
- Non-predictive, pure statistical analysis of player performance
- Independent page with separate player search and data loading
- No dependencies on Player Analysis page

**Features:**
1. **Independent Player Search:**
   - Dedicated search bar in Season Report sidebar
   - Season and type (Regular/Playoffs) selection
   - Separate API calls and data storage
   - No need to visit Player Analysis first

2. **Date Range Filtering:**
   - **Full Season:** View all games in selected season
   - **Monthly:** Filter by specific months within season
   - **Custom Date Range:** Select any date range within season boundaries
   - Automatic date constraints based on season selection

3. **Descriptive Statistics Dashboard:**
   - Quick metrics grid: Mean values for PTS, REB, AST, 3PM, Minutes
   - Detailed statistics table with Mean, Median, Std Dev, Min, Max
   - Game count for each filtered period
   - Export-ready format

4. **Performance Trend Visualizations:**
   - Line charts for Points, Rebounds, Assists over time
   - Red dashed average line for reference
   - Interactive Plotly charts with hover details
   - Date-based X-axis for temporal analysis

5. **Monthly Comparison (Full Season View):**
   - Grouped bar chart comparing monthly averages
   - Side-by-side comparison of PTS, REB, AST
   - Only shown when viewing full season with 5+ games
   - Helps identify performance trends across months

6. **Game Log & Anomaly Detection:**
   - **Automatic anomaly detection:**
     - 🔴 DNP/Low Minutes: Games with <5 minutes played
     - 🔥 High Performance: Stats >2 standard deviations above mean
     - ❄️ Low Performance: Stats >2 standard deviations below mean
   - **Anomaly summary table:**
     - Date, Type, and Detail for each anomaly
     - Counts total anomalies detected
     - Helps identify injury games, outlier performances
   - **Full game log:**
     - Expandable table with all games in filtered period
     - Shows: Date, PTS, REB, AST, 3PM, FG%, MIN
     - Sorted by date (most recent first)

**Technical Implementation:**
- New function: `show_season_report_page(api_client, stats_engine, player_data)`
- File: `app.py` (lines 39-306)
- Uses pandas for data manipulation and aggregation
- Plotly for interactive visualizations
- Session state: `report_player_data` (separate from main player data)

**User Workflow:**
1. Click "📅 Season Report" in sidebar navigation
2. Search for player in Season Report sidebar
3. Select season and type (Regular/Playoffs)
4. Click "Load for Report"
5. Choose filtering: Full Season, Monthly, or Custom Date Range
6. Explore statistics, charts, trends, and anomalies

**Impact:**
- ✅ Pure descriptive analysis without prediction complexity
- ✅ Historical performance tracking and trend identification
- ✅ Anomaly detection helps identify context (injuries, rest days)
- ✅ Independent from predictive features - clean separation
- ✅ Foundation for scouting reports and player evaluation

### UI Simplification - Academic Sections Removed ✨ NEW (October 18, 2025)
**Major User Experience Improvement:**
- Simplified Player Analysis page by removing academic clutter
- Focus on actionable insights over statistical details

**Removed Sections:**
1. ❌ **"🎯 Performance Insights"** - Entire section removed
   - Was showing threshold-based pattern analysis
   - Had toggle for "Detailed Analysis" 
   - Academic probability tables and insights
   - Deemed unnecessary for user decision-making

2. ❌ **"Fixed Thresholds Analysis"** - Removed from default view
   - Complex bar charts showing frequency vs cool-off
   - Academic probability tables
   - Statistical threshold analysis

3. ❌ **"Dynamic Thresholds (Player-Specific)"** - Removed
   - μ+σ, μ+2σ, μ+3σ threshold tables
   - Cool-off probabilities at dynamic thresholds
   - Technical statistical breakdowns

4. ❌ **"Frequency vs Cool-off Probability"** charts - Removed
   - Academic visualization of probability distributions
   - Too technical for general users

**What Remains:**
- ✅ Season Statistics (clean metrics display)
- ✅ Recent Game Performance (game table)
- ✅ Career Phase & Fatigue Analysis (visual charts)
- ✅ Next Game Predictions (main prediction cards)
- ✅ Quick Betting Guide (actionable recommendations)
- ✅ Player Comparison (side-by-side analysis)

**Technical Changes:**
- Line 747 in `app.py`: Section replaced with comment
- All probability calculation logic moved to background
- Results still used by prediction cards, just not displayed separately

**Impact:**
- ✅ Cleaner, more focused interface
- ✅ Reduced cognitive load for users
- ✅ Faster navigation to actionable predictions
- ✅ Better user experience for non-technical users
- ✅ Maintains all statistical rigor in background calculations

### Simple Prediction Cards Enhancement ✨ NEW (October 18, 2025)
**Cleaner Prediction Display:**
- Removed cluttered "faded descriptions" from Simple View mode
- Streamlined user interface for better readability

**Removed Elements:**
1. ❌ **"📊 5/10 recent games"** caption - Removed
2. ❌ **"⚠️ MEDIUM confidence"** caption - Removed
3. ❌ **"🔴 HIGH risk"** caption - Removed

**Current Simple View Display:**
```
🎯 Points ≥ 20
❌ UNLIKELY (75% confidence)    🔥 HOT    💡 BET: UNDER

💡 Player showing strong regression - points likely below average level
```

**What Remains:**
- ✅ Main prediction (LIKELY/UNLIKELY with percentage)
- ✅ Performance indicator (HOT/COLD/STEADY/VOLATILE)
- ✅ Betting recommendation (OVER/UNDER/NEUTRAL/AVOID)
- ✅ Actionable insight (clear explanation)
- ✅ Quick Betting Guide section (preserved as requested)

**Technical Changes:**
- File: `components/simple_prediction_cards.py`
- Lines 134-146: Removed details row with captions
- Replaced with comment: "# Details row removed - keeping it simple"

**User Preference System:**
- Technical users can still access full details in technical view
- Simple view toggle provides clean, actionable information
- Betting guide maintained for quick decision-making

**Impact:**
- ✅ Much cleaner interface without distracting details
- ✅ Focus on core prediction and recommendation
- ✅ Better mobile viewing experience
- ✅ Faster comprehension of key information
- ✅ Maintains all calculation accuracy in background

### Opponent Team Tracking in Season Report ✨ NEW (October 18, 2025)
**Enhanced Context for Game Analysis:**
- Added opponent team information to all game displays in Season Report
- Shows home/away designation with clear indicators

**Features:**
1. **Opponent Column in Game Log:**
   - Format: `vs LAL` (home game) or `@ BOS` (away game)
   - `vs` = playing at home against opponent
   - `@` = playing away at opponent's arena
   - Shows team abbreviations (e.g., LAL, BOS, GSW)

2. **Opponent in Anomaly Detection:**
   - Anomaly table now includes opponent team
   - Helps identify matchup-specific patterns
   - Example: "🔥 High Points @ LAL - Player excels against this team"

3. **Full Game Log with Opponents:**
   - All games display includes opponent column
   - Sortable by date, opponent, or any stat
   - Format: Date | Opponent | PTS | REB | AST | 3PM | FG% | MIN

**How It Works:**
- Extracts `home_team` and `visitor_team` from API game data
- Compares with player's team ID to determine opponent
- Automatically determines home/away status
- Displays in clean, consistent format

**Technical Implementation:**
- File: `app.py` (lines 67-94, 280-306, 319-324)
- Uses nested game object: `game.get('game', {}).get('home_team')`
- Determines opponent by comparing team IDs
- Adds `opponent` field to games DataFrame

**Use Cases:**
- Identify teams player performs well against
- Spot matchup-specific anomalies
- Analyze home vs away performance patterns
- Context for DNP or low-minute games

**Impact:**
- ✅ Richer context for performance analysis
- ✅ Enables matchup-specific insights
- ✅ Better understanding of anomalies
- ✅ Foundation for opponent-based filtering

### Opponent-Specific Prediction Filtering ✨ NEW (October 18, 2025)
**Matchup-Based Prediction Analysis:**
- Filter predictions based on past performance against specific opponent
- Toggle on/off to compare general vs matchup-specific predictions

**Features:**
1. **Filter by Opponent Toggle:**
   - Located at top of "Next Game Predictions" section
   - 🏀 Toggle button: "Filter by Opponent"
   - Optional feature - predictions work normally when disabled
   - Clean two-column layout (toggle + dropdown)

2. **Opponent Team Text Input:**
   - Free-form text input for team abbreviation (e.g., LAL, BOS, GSW)
   - Allows entering next opponent even if not in historical data
   - Automatically converts to uppercase for consistency
   - Shows helpful caption with teams from player's history

3. **Filtered Prediction Analysis:**
   - Uses only **last 3 games** against selected opponent (most recent matchups)
   - Automatically sorts by date to get most recent games
   - Shows informative messages:
     - "✅ Using **last 3 games** against **LAL** (found 5 total)"
     - "✅ Using **2 game(s)** against **BOS**" (if fewer than 3)
   - All prediction models respect the filter:
     - Inverse-frequency probabilities
     - Career phase weighting (if enabled)
     - Bayesian smoothing
     - Confidence levels

4. **Smart Handling:**
   - Warning if no games found against opponent
   - Falls back to all games if insufficient data
   - Works with career phase decay toggle
   - Respects custom thresholds from Advanced Settings

**How It Works:**
```python
# Extract opponents from recent games
for game in recent_games:
    home_team = game['game']['home_team']
    visitor_team = game['game']['visitor_team']
    # Determine which is opponent based on player's team

# Filter games against selected opponent
opponent_games = [g for g in games if opponent_matches(g, selected_team)]

# Sort by date and take only last 3 games
opponent_games.sort(key=lambda x: x['game']['date'], reverse=True)
filtered_games = opponent_games[:3]  # Most recent 3 matchups

# Use filtered games for all predictions
games_df = pd.DataFrame(filtered_games)
probability_results = model.calculate_inverse_frequency_probabilities(
    games_df, thresholds, alpha=alpha
)
```

**Technical Implementation:**
- File: `app.py` (lines 1137-1169)
- Text input field with placeholder and help text
- Extracts opponents from history as helpful reference
- Accepts any team abbreviation (not limited to history)
- Filters games by comparing home/visitor team IDs
- Sorts by date (most recent first) using `sort(key=lambda x: x['game']['date'], reverse=True)`
- Takes only last 3 games: `opponent_games[:3]`
- Updates `games_df` to use `filtered_recent_games`
- All downstream predictions automatically use filtered data

**Use Cases:**
- **Pre-game Analysis:** "How does LeBron perform against the Warriors?"
- **Betting Strategy:** Compare predictions vs specific matchups
- **Matchup Advantages:** Identify favorable/unfavorable opponents
- **Context-Aware Predictions:** Account for defensive matchups

**Example Workflow:**
1. Load player (e.g., LeBron James)
2. Toggle "🏀 Filter by Opponent" ON
3. Type "GSW" in the text input field
4. Predictions automatically recalculate using games vs Warriors
5. Compare with toggle OFF to see general predictions
6. Can enter ANY team abbreviation (even if not in history)

**Impact:**
- ✅ Matchup-specific prediction accuracy
- ✅ More informed betting decisions
- ✅ Identifies opponent-specific patterns
- ✅ Complements existing prediction models
- ✅ No interference when disabled - optional enhancement

**Edge Cases Handled:**
- No games vs opponent → Warning + fallback to all games
- Insufficient games (<3) → Uses available data with Bayesian smoothing
- No opponent data in API → Graceful degradation, feature disabled
- Multiple games vs same opponent → All included in analysis

---

## 📝 Earlier Implementation Updates (October 2025)

### Python 3.11 Upgrade ⚡
**Major Infrastructure Improvement:**
- Upgraded from Python 3.7 to Python 3.11+
- **Benefits**:
  - Better package compatibility (eliminated DLL crashes)
  - Improved performance (10-60% faster than 3.7)
  - Enhanced error messages for debugging
  - Better type checking support
  - Latest security patches
- **Breaking Changes**: None for end users
- **Migration**: Fresh virtual environment recommended
- Streamlit now runs reliably without DLL access violations
- All dependencies updated to compatible versions

### Launcher Scripts ✨
**New Application Launchers:**
- `launch.py`: Cross-platform Python launcher with error handling
- `run_app.bat`: Windows batch file for one-click startup
- Automatic virtual environment detection
- Helpful error messages for missing dependencies
- Status output showing Python path and app location

### Project Cleanup 🧹
**Repository Organization:**
- Created comprehensive `.gitignore` (excludes env/, cache, etc.)
- Removed test files from production
- Removed Replit-specific files
- Added comprehensive `README.md`
- Streamlined startup process

### Comprehensive Error Handling System 🛡️
**Major UX/Reliability Improvement (October 2025):**
- **New Module:** `error_handler.py` with 8 utility functions
- **Safe API Wrapper:** `safe_api_call()` for graceful failure handling
- **User Experience:**
  - Loading spinners for all operations: "⏳ Loading LeBron James..."
  - Success confirmations: "✅ Successfully loaded player!"
  - Clear error messages: "❌ Unable to load player. Try different season."
  - Actionable suggestions when data is missing
- **Connection Monitoring:**
  - Live API health check in sidebar
  - API call count tracking
  - Connection status indicator (🌐)
- **Data Quality Warnings:**
  - Automatic warnings for limited samples (<5 games)
  - Empty data detection with helpful suggestions
  - Missing season data guidance
  - Bayesian smoothing notices for small samples
- **Graceful Degradation:**
  - App continues functioning when API fails
  - Default returns for failed calls
  - Retry logic with exponential backoff
  - No silent failures - always user feedback

**Error Handler Functions:**
```python
safe_api_call()           # Wrapper for API calls with default returns
show_loading()            # Context manager for loading spinners
validate_player_data()    # Validates required fields exist
show_connection_status()  # Displays API health in sidebar
show_data_quality_warning()  # Warns about insufficient data
handle_empty_data()       # Provides helpful suggestions
retry_operation()         # Retry logic with exponential backoff
```

**Implementation Coverage:**
- ✅ All player data loading (main, favorites, comparison)
- ✅ Season statistics fetching
- ✅ Recent games retrieval
- ✅ Career stats loading
- ✅ Player search operations

**Impact:**
- Before: Generic errors, silent failures, no loading feedback
- After: Clear messages, helpful guidance, graceful degradation
- Result: Significantly improved user experience and reliability

## 📝 Feature Implementation Details

### Career Phase Decay Toggle ✨
**Advanced Feature Added:**
- Toggle in Advanced Settings: "Enable Career Phase Decay"
- When enabled, predictions use comprehensive regression model
- Auto-detects career phase from player stats:
  - Early (🌱): ≤3 seasons, learning/improving
  - Rising (📈): Positive trend >0.5 PPG/year
  - Peak (⭐): Stable performance, >3 seasons
  - Late (🌅): ≥10 seasons with decline >-0.5 PPG/year
  - Unknown (❓): Insufficient data
- Lambda decay parameters (disabled when toggle OFF):
  - λ Early: 0.02 (less decay, recent games weighted more)
  - λ Peak: 0.05 (balanced weighting)
  - λ Late: 0.08 (more decay, regression tendency)
- Career phase indicator shown: "[emoji] Career Phase: [Phase]"
- Uses `career_weighted_frequency` when enabled
- Includes fatigue, minutes, and non-stationarity adjustments

### Next Game Predictions Feature ✨
**New Section Added:**
- Header: "🔮 Next Game Predictions"
- Displays success probability for each custom threshold
- Example: "≥ 20 points: 65% (Confidence: High)"
- Uses `weighted_frequency` from inverse-frequency model (or `career_weighted_frequency` if career phase enabled)
- Applies Bayesian smoothing for samples <10 games
- Shows confidence levels: High (≥5 occurrences) or Low (<5 occurrences)
- Recency weighted with configurable α parameter (default 0.85)
- Expandable info guide explains probability calculations
- Configured via Advanced Settings thresholds

### API Data Structure Changes
**Minutes Field Format:**
- API returns minutes as **"MM:SS" string** (e.g., "34:08" = 34 minutes 8 seconds)
- Implemented `parse_minutes()` function to convert to decimal: `34:08 → 34.13`
- Applied parsing in:
  - Display metrics (app.py)
  - Z-score calculations (statistics.py)
  - Chart plotting (plotly visualizations)

### Season Display Format
**NBA Convention Adopted:**
- Changed from single year ("2024") to full season format ("2024-2025")
- Updated in all selectors: main, favorites, comparison
- Season Statistics header shows full format
- Backend API still uses base year (2024-2025 → API request with year=2024)

### Data Availability
**2024-2025 Season:**
- ✅ Confirmed data available from October 2024 through April 2025
- Request `per_page=100` to fetch complete season before sorting
- Recent games charts display 2025 dates correctly
- All numeric conversions use `pd.to_numeric()` and `safe_float()`

**Historical Seasons:**
- Supports 2020-2021 through 2024-2025 seasons
- Playoffs vs Regular Season toggle for all seasons
- Consistent data structure across seasons
- Automatic caching for performance

### Current Tech Stack (Updated October 2025)
- ✅ **Frontend**: Streamlit 1.23+ (Production-ready)
- ✅ **Backend**: Direct API integration (no FastAPI/Flask layer)
- ✅ **Data Source**: balldontlie.io API v1
- ✅ **Computation**: NumPy, Pandas, SciPy
- ✅ **Visualization**: Plotly (express & graph_objects)
- ✅ **Persistence**: SQLite (caching + favorites)
- ✅ **Python**: 3.11+ (Upgraded from 3.7)
- ✅ **Deployment**: Local with launcher scripts

### Implemented Formulas & Assumptions

**Inverse-Frequency Model:**
```
P_inv(x) = 1 - f(x)
f(x) = (1/N) * Σ I[stat_i ≥ t]
```
- Applied with Bayesian smoothing (α=1, β=1) for samples <10 games
- Supports dynamic thresholds: {μ, μ+σ, μ+2σ, μ+3σ}

**Career Phase Weighting:**
```
w_i = e^(-λ(T - t_i))
λ_early = 0.02 (default)
λ_peak = 0.05 (default)  
λ_late = 0.08 (default)
```

**Z-Score Normalization:**
```
z = (x - μ_season) / σ_season
```
- Applied to: PTS, REB, AST, FG%, 3P%, FT%, MIN
- League averages calculated from season data

**Recency Weighting:**
```
α = 0.85 (default, configurable 0.5-1.0)
w_i = α^(N-i)
```

**Fatigue Analysis:**
- 10-game rolling average vs long-term mean
- Regression risk = (current - mean) / std_dev
- Minutes trend detection with linear regression  

---

## 🚀 Running the Application

### Quick Start
```bash
# Method 1: Using Python launcher (Recommended)
python launch.py

# Method 2: Using batch file (Windows)
run_app.bat

# Method 3: Direct Streamlit command
streamlit run app.py
```

The application will start on **http://localhost:8501**

### Python Version Requirements
- **Minimum**: Python 3.7
- **Recommended**: Python 3.11+
- Python 3.11 provides better package compatibility and performance

### Environment Setup Issues
If you encounter DLL crashes or import errors on Python 3.7:
1. Upgrade to Python 3.11: `python --version`
2. Create fresh virtual environment: `python -m venv env`
3. Install dependencies: `pip install -r requirements.txt`

### Configuration
Edit `.streamlit/config.toml` to customize:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 8501

[theme]
base = "light"
```

---

## 🧩 End Objective
✅ **ACHIEVED**: Delivered a statistically grounded NBA performance predictor that quantifies regression likelihood per player and visualizes trends interactively.

**Current Status**: Production-ready Streamlit application with comprehensive statistical modeling, player comparison, favorites management, and data export capabilities.

**Foundation Established For**:
- Future predictive and simulation-based analytics
- Machine learning model integration
- React/TypeScript frontend migration
- Multi-sport expansion
- Real-time game predictions
