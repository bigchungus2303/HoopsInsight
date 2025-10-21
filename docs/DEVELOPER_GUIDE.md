# 🔧 Developer Guide - HoopsInsight

**Complete technical documentation for developers**

Last Updated: October 20, 2025

---

## 📁 Project Structure

```
HoopsInsight/
├── 🎯 Entry Points
│   ├── app.py                 # Main Streamlit application
│   ├── launch.py              # Cross-platform launcher
│   └── run_app.bat            # Windows batch launcher
│
├── 🧮 Core Modules
│   ├── nba_api.py            # NBA API client with schema-versioned caching
│   ├── cache_sqlite.py       # Schema-versioned SQLite cache (NEW)
│   ├── database.py           # SQLite database operations (favorites, predictions)
│   ├── models.py             # Statistical models (Inverse-Frequency, Bayesian)
│   ├── statistics.py         # Statistical calculations
│   ├── config.py             # Configuration
│   ├── logger.py             # Logging
│   ├── error_handler.py      # Error handling
│   └── export_utils.py       # Data export (CSV/JSON)
│
├── 🧩 UI Components
│   └── components/
│       ├── api_dashboard.py        # API usage stats
│       ├── advanced_settings.py    # Single threshold per stat
│       ├── prediction_cards.py     # Technical view
│       ├── simple_prediction_cards.py  # Simple view
│       ├── charts.py               # Plotly charts
│       └── lambda_advisor.py       # AI parameter optimization
│
├── 🧪 Tests
│   └── tests/
│       ├── test_models.py          # Model tests (13 tests)
│       ├── test_statistics.py      # Statistics tests (12 tests)
│       └── test_error_handling.py  # Error handling tests
│
└── 📚 Documentation
    ├── README.md                    # Main user guide
    ├── DEVELOPER_GUIDE.md           # This file
    ├── CHANGELOG.md                 # Feature history
    └── attached_assets/nba-stats-mvp.md  # Master specification
```

---

## 🗄️ Database Architecture

### **Two Database Systems:**

#### **1. cache.db** (NEW - Schema Versioned)
**Purpose:** HTTP cache with automatic schema validation

**Table:**
```sql
CREATE TABLE http_cache (
    key TEXT PRIMARY KEY,           -- SHA256 hash of namespace+params+schema
    payload TEXT NOT NULL,          -- JSON serialized response
    updated_at INTEGER NOT NULL,    -- Unix timestamp
    schema_ver TEXT NOT NULL        -- e.g., "games:v2"
)
```

**Features:**
- Schema versioning (auto-invalidates on field changes)
- TTL-based expiration (6 hours for games, 24 hours for teams)
- Required fields validation: `{id, date, home_team_id, visitor_team_id}`
- Deterministic cache keys (parameter order doesn't matter)

**Usage:**
```python
from cache_sqlite import cache_key, get_cached, set_cached, SCHEMA_VER

# Generate key
key = cache_key("balldontlie:games", {"player_id": 115, "season": 2024}, SCHEMA_VER)

# Try cache
cached = get_cached(key)
if cached:
    return cached["games"]

# Fetch from API, validate, cache
games = fetch_from_api()
validate_games_schema(games)
set_cached(key, {"games": games}, SCHEMA_VER)
```

#### **2. nba_cache.db** (Legacy - User Data)
**Purpose:** User preferences and prediction tracking

**Tables:**
- `favorites` - User's favorite players
- `predictions` - Saved predictions for validation
- `prediction_metrics` - Aggregate accuracy tracking

---

## 🔄 API Client Architecture

### **NBAAPIClient** (`nba_api.py`)

**Key Methods:**
```python
# Player data
search_players(query, limit=10) → List[Dict]
get_player_info(player_id) → Dict

# Season data
get_season_stats(player_id, season, postseason=False) → Dict
get_recent_games(player_id, limit=100, season, postseason=False) → List[Dict]
get_career_stats(player_id, postseason=False) → List[Dict]

# Team data
get_teams() → Dict[int, str]  # team_id → abbreviation
get_all_teams_details() → List[Dict]  # Full team info for autocomplete
```

**Caching Strategy:**
- Uses `cache_sqlite.py` for HTTP responses
- Schema validation on all game data
- Auto-recovery from validation failures
- 6-hour TTL for games, 24-hour for teams

---

## 📊 Statistical Models

### **InverseFrequencyModel** (`models.py`)

**Core Probability Calculation:**
```python
P(stat ≥ threshold) = weighted_frequency

weighted_frequency = Σ(weights[i] × exceeds[i])

weights[i] = α^(N - i - 1) / Σ(α^(N - j - 1))
```

**Key Parameters:**
- **α (alpha)**: Recency weight (0.5 to 1.0)
  - 0.50-0.75: Trust recent form (hot streaks)
  - 0.85 (default): Balanced approach
  - 1.00: Pure average (all games equal)

- **λ (lambda)**: Career phase decay
  - Early career: 0.02 (trust growth)
  - Peak career: 0.05 (balanced)
  - Late career: 0.08 (trust recent decline)

**Methods:**
```python
calculate_inverse_frequency_probabilities(games_df, thresholds, alpha=0.85)
calculate_comprehensive_regression_model(games_df, season_stats, career_phase, thresholds, lambda_params)
analyze_fatigue_curve(games_df, window_size=10)
analyze_minutes_trend(games_df)
```

---

## 🧪 Testing

### **Run All Tests:**
```bash
python run_tests.py
```

### **Test Suites:**

**test_models.py** (13 tests)
- Recency weight calculation
- Inverse frequency probabilities
- Confidence intervals
- Bayesian smoothing
- Minutes trend detection

**test_statistics.py** (12 tests)
- Z-score normalization
- Career phase weights
- Consistency metrics
- Outlier detection

**test_error_handling.py**
- Safe API calls
- Error recovery
- Data validation

**cache_sqlite.py** (7 self-tests)
```bash
python cache_sqlite.py
```
- Database initialization
- Cache key determinism
- TTL expiry
- Schema version mismatch
- Field validation

---

## 🔧 Development Workflow

### **1. Making Changes**

**Before coding:**
```bash
# Always read the master spec
cat attached_assets/nba-stats-mvp.md
```

**When changing model logic:**
1. Update formulas in code
2. Update `attached_assets/nba-stats-mvp.md`
3. Add tests
4. Update this guide

**When adding features:**
1. Implement in appropriate module
2. Add to `CHANGELOG.md`
3. Update `README.md` if user-facing
4. Run tests

### **2. Cache Schema Changes**

**If you need to add/change required fields:**

```python
# In cache_sqlite.py
SCHEMA_VER = "games:v3"  # Bump version
REQUIRED_FIELDS = {"id", "date", "home_team_id", "visitor_team_id", "new_field"}

# In nba_api.py - update normalization
normalized = {
    "id": game_info.get("id"),
    "date": game_info.get("date"),
    "home_team_id": game_info.get("home_team_id"),
    "visitor_team_id": game_info.get("visitor_team_id"),
    "new_field": game_info.get("new_field"),  # Add new field
    # ...
}
```

Old cache automatically invalidated!

### **3. Adding New Components**

Create in `components/`:
```python
# components/my_component.py
import streamlit as st

def show_my_component(data):
    """Display my component"""
    st.subheader("My Component")
    # ... implementation
```

Import in `app.py`:
```python
from components.my_component import show_my_component
```

---

## 🏗️ Architecture Patterns

### **Separation of Concerns**

**Data Layer** (`nba_api.py`, `cache_sqlite.py`, `database.py`)
- API calls
- Caching
- Data persistence

**Business Logic** (`models.py`, `statistics.py`)
- Statistical calculations
- Probability models
- Analysis algorithms

**Presentation** (`app.py`, `components/`)
- UI rendering
- User interactions
- Visualizations

### **Error Handling**

Use `safe_api_call` wrapper:
```python
from error_handler import safe_api_call

# Automatically handles errors, shows user-friendly messages
games = safe_api_call(
    api_client.get_recent_games,
    player_id, limit=100,
    default_return=[],
    error_message="Unable to load games"
)
```

### **Session State Management**

Store user selections:
```python
st.session_state.selected_player = player
st.session_state.player_data = {
    'player': player,
    'season_stats': season_stats,
    'recent_games': recent_games
}
```

---

## 🎨 UI Component Guidelines

### **Tooltips**
- Keep single-line with pipe separators
- Use emojis sparingly
- Examples: `"🔥 Low: Hot streak  |  ⚖️ Medium: Balanced  |  📊 High: Average"`

### **Metrics**
- Simple, no technical jargon
- Remove Z-scores, confidence labels
- Show only percentage or value

### **Settings**
- Single threshold per category (not 4)
- Number inputs for precision
- Clear help text

---

## 🐛 Common Issues

### **Opponent Filter Not Working**

**Symptom:** "No games vs SAC found" when games exist

**Root Cause:** Old cache missing `home_team_id`/`visitor_team_id`

**Solution:**
1. Enable opponent filter
2. Click "🔄 Clear Cache"
3. Reload player data
4. Try opponent filter again

### **Schema Validation Errors**

**Error:**
```
ValueError: CACHE_SCHEMA_MISMATCH: Game 0 missing fields: {'home_team_id'}
```

**What it means:** Good! Cache detected incomplete data

**Auto-recovery:**
1. Cache automatically cleared
2. Fresh data fetched from API
3. Re-validated and cached

**If persists:**
- Check API response structure
- Verify normalization code in `nba_api.py`

### **Import Errors**

**Fix:**
```bash
pip install -r requirements.txt
```

Or with virtual environment:
```bash
.\env\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 🚀 Deployment Checklist

- [ ] All tests pass (`python run_tests.py`)
- [ ] Cache tests pass (`python cache_sqlite.py`)
- [ ] No linter errors
- [ ] README.md updated
- [ ] CHANGELOG.md updated if features added
- [ ] Master spec updated if model changed
- [ ] Clear cache.db before deployment (optional)

---

## 📝 Code Style

- Follow existing patterns
- Use type hints where appropriate
- Add docstrings to functions
- Keep functions focused (single responsibility)
- Comment complex algorithms
- Use meaningful variable names

---

## 🔗 Key Files Reference

| File | Purpose | When to Modify |
|------|---------|----------------|
| `nba-stats-mvp.md` | Master specification | Model logic changes |
| `cache_sqlite.py` | Cache library | Schema changes |
| `nba_api.py` | API client | API endpoint changes |
| `models.py` | Statistical models | Formula changes |
| `components/advanced_settings.py` | User settings | Threshold/parameter changes |
| `app.py` | Main application | UI/flow changes |

---

## 📞 Getting Help

1. Check this guide first
2. Read master spec: `attached_assets/nba-stats-mvp.md`
3. Check `CHANGELOG.md` for recent changes
4. Review test files for usage examples

---

**Happy coding!** 🚀

