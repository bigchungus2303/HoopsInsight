# 📝 Changelog - HoopsInsight

All notable changes and features for the NBA Performance Predictor.

---

## [Latest] - October 20, 2025

### ✨ Added
- **Schema-Versioned Cache System** (`cache_sqlite.py`)
  - Auto-invalidates on schema changes
  - Required fields validation: `{id, date, home_team_id, visitor_team_id}`
  - TTL-based expiration (6h games, 24h teams)
  - Deterministic SHA256 cache keys
  - Self-tests included

- **Opponent Team Autocomplete**
  - Type "L" → Shows Lakers (LAL), Clippers (LAC), etc.
  - Search by team name, city, or abbreviation
  - No need to memorize abbreviations

- **Alpha Impact Visualizer**
  - "🔍 Show α Impact" checkbox
  - Compare weighted vs unweighted probabilities
  - See if recency weight actually affects predictions

- **3-Point Stats in Season Report**
  - Added to Performance Trends charts
  - Added to Monthly Comparison
  - Added to Anomaly Detection

### 🔧 Changed
- **Load ALL Season Games** (not just 20)
  - Changed from `limit=20` to `limit=100`
  - Opponent filter uses ALL games vs team (not just last 3)
  - Better historical matchup analysis

- **Simplified Advanced Settings**
  - Single threshold per category (was 4 sliders each)
  - Cleaner 2-column layout
  - Clear tooltips with examples

- **Removed Technical Jargon**
  - No more "Z-Score: X.XX" in season stats
  - No more "🟢 High confidence" in predictions
  - Just clean numbers and percentages

- **Simplified Minutes Analysis**
  - Removed fatigue/load curve
  - Kept only minutes trend chart
  - Focus on playing time sustainability

### 🐛 Fixed
- **Opponent Filter Cache Issue**
  - Old cache missing team IDs → SAC filter failing
  - New cache validates all required fields
  - Auto-recovery from schema mismatches

### 📊 Sample Size Warnings
- ⚠️ Warning if < 3 games vs opponent
- 🚨 Error if < 2 games
- Clear messaging about reliability

---

## [October 18, 2025] - Major Feature Release

### ✨ Added
- **Prediction History Page**
  - Save predictions for tracking
  - Verify after games
  - Track model accuracy over time
  - 3-tab interface (Metrics, Recent, Verify)

- **Season Report Page**
  - Independent player search
  - Custom date filtering (monthly, custom range)
  - Descriptive statistics (mean, median, std dev)
  - 4 performance trend charts
  - Monthly comparison charts
  - Game log with anomaly detection

- **AI Lambda Advisor**
  - Auto-calculate optimal λ parameters
  - Career phase detection
  - "✨ Auto" button for one-click optimization
  - Confidence ratings and reasoning

- **Interactive Threshold Controls**
  - Visual slider controls (later simplified to single input)
  - Live threshold adjustment
  - Immediate prediction updates

- **API Usage Dashboard**
  - Real-time cache hit rate
  - Total API calls tracking
  - Performance monitoring

### 🔧 Changed
- **Modularized app.py**
  - Refactored 1091 lines → 860 lines
  - Created reusable components
  - Better code organization

- **Three-Page Navigation**
  - Player Analysis (predictive)
  - Season Report (descriptive)
  - Prediction History (validation)

### 📚 Documentation
- Created 13 documentation files in `docs/`
- Comprehensive feature guides
- Database architecture docs
- Testing guides

---

## [Earlier 2025] - Core Application

### ✨ Features
- **Player Search & Analysis**
  - Autocomplete player search
  - Season statistics display
  - Recent game performance charts
  - Career phase weighting

- **Inverse-Frequency Model**
  - Regression-to-mean analysis
  - Recency weighting (α parameter)
  - Bayesian smoothing for small samples
  - Dynamic threshold calculations

- **Player Comparison**
  - Side-by-side analysis
  - Comparative charts
  - Season vs season comparison

- **Data Export**
  - CSV export
  - JSON export
  - Probability analysis export

- **Favorites System**
  - Save favorite players
  - Quick access from sidebar
  - Persistent storage

### 🔧 Technical
- SQLite caching for API responses
- Streamlit-based UI
- Plotly interactive charts
- Error handling and recovery
- Logging system

---

## 🎯 Breaking Changes

### October 20, 2025
- **Cache system replaced:** `nba_cache.db` → `cache.db` for HTTP caching
- **Must clear old cache** on first load after update
- **Advanced Settings UI changed:** 4 sliders → 1 input per stat

### October 18, 2025
- **Pages moved inline:** Removed `pages/` imports (defined in app.py)
- **Session state structure:** Added page-specific data isolation

---

## 🔮 Upcoming Features

**Planned:**
- Player news integration (on hold)
- Multi-season opponent analysis
- Advanced betting tools
- Performance prediction ML models
- Real-time game tracking

---

## 📊 Statistics

**Total Features:** 30+
**Lines of Code:** ~3,500
**Test Coverage:** 25+ unit tests
**Documentation:** 4 core docs
**Cache Performance:** ~90% hit rate

---

## 🤝 Contributing

When adding features:
1. Read `attached_assets/nba-stats-mvp.md`
2. Update code with tests
3. Add entry to this CHANGELOG
4. Update README.md if user-facing
5. Update DEVELOPER_GUIDE.md if technical

---

**For detailed technical information, see DEVELOPER_GUIDE.md**

