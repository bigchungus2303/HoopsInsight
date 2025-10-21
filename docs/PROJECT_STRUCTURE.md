# Project Structure

## 📂 Organized Directory Layout

```
HoopsInsight/
├── 📄 Root Files (Launchers & Config)
│   ├── app.py                    # Main Streamlit application
│   ├── launch.py                 # Cross-platform launcher
│   ├── run_app.bat               # Windows quick launch
│   ├── run_tests.py              # Test runner
│   ├── README.md                 # Main documentation
│   ├── requirements.txt          # Python dependencies
│   ├── pyproject.toml            # Project metadata
│   ├── runtime.txt               # Python version (deployment)
│   ├── packages.txt              # System dependencies (deployment)
│   └── healthcheck.py            # Health check endpoint
│
├── 🧠 Core Modules (Business Logic)
│   ├── nba_api.py                # NBA API client with caching
│   ├── database.py               # SQLite database operations
│   ├── models.py                 # Statistical models (Inverse-Frequency, Bayesian)
│   ├── statistics.py             # Statistical calculations
│   ├── config.py                 # Configuration constants
│   ├── cache_sqlite.py           # Schema-versioned HTTP cache
│   ├── logger.py                 # Logging infrastructure
│   ├── error_handler.py          # Error handling utilities
│   └── export_utils.py           # Data export (CSV/JSON)
│
├── 🎨 components/ (UI Components)
│   ├── __init__.py
│   ├── advanced_settings.py      # Threshold & settings UI
│   ├── prediction_cards.py       # Prediction display
│   ├── simple_prediction_cards.py # Simplified cards
│   ├── lambda_advisor.py         # AI lambda recommendations
│   └── api_dashboard.py          # API usage stats (hidden)
│
├── 📄 pages/ (Streamlit Pages)
│   └── pick_of_the_day.py        # Pick of the Day page ✨
│
├── ⚙️ services/ (Business Services)
│   ├── __init__.py
│   └── picks.py                  # Pick of the Day service ✨
│
├── 🔧 pick_configs/ (Pick Configuration)
│   ├── __init__.py
│   └── picks.yaml                # Market presets & filters ✨
│
├── 📊 data/ (Data Files)
│   ├── nba_2025_2026_schedule.csv # NBA schedule (move here) ✨
│   └── README.md                 # Data documentation
│
├── 🧪 tests/ (Unit Tests)
│   ├── __init__.py
│   ├── README.md
│   ├── test_models.py
│   ├── test_statistics.py
│   ├── test_error_handling.py
│   └── test_picks.py             # Pick tests ✨
│
├── 📚 docs/ (Documentation)
│   ├── README.md                 # Documentation index
│   ├── PICK_OF_THE_DAY_README.md # Pick feature guide ✨
│   ├── DEVELOPER_GUIDE.md        # Developer guide
│   ├── CHANGELOG.md              # Feature changelog
│   ├── DEPLOY_TO_AEO_INSIGHTS.md # Deployment guide
│   ├── DISCLAIMER.md             # Legal disclaimer
│   ├── PRIVACY.md                # Privacy policy
│   ├── TERMS.md                  # Terms of service
│   └── SECURITY.md               # Security policy
│
├── 🎨 attached_assets/ (Project Assets)
│   ├── nba-stats-mvp.md          # Main specification
│   └── image_*.png               # Screenshots
│
├── ⚙️ .streamlit/ (Streamlit Config)
│   ├── config.toml               # App configuration
│   └── secrets.toml              # API keys (gitignored)
│
└── 💾 Cache (Auto-generated, gitignored)
    ├── nba_cache.db              # User data (favorites, predictions)
    └── cache.db                  # HTTP cache
```

## 📁 Directory Purpose

| Directory | Purpose | Files |
|-----------|---------|-------|
| **Root** | Launchers, main app, core modules | 15+ files |
| **components/** | Reusable UI components | 6 files |
| **pages/** | Streamlit page modules | 1 file |
| **services/** | Business logic services | 1 file |
| **pick_configs/** | Pick of the Day configuration | 1 YAML |
| **data/** | Data files (schedules, etc.) | 1+ CSV |
| **tests/** | Unit tests | 5 test files |
| **docs/** | All documentation | 9 MD files |
| **attached_assets/** | Specification & images | 2+ files |
| **.streamlit/** | Streamlit configuration | 2 files |

## 🗂️ File Categories

### Entry Points
- `app.py` - Main Streamlit application
- `launch.py` - Python launcher
- `run_app.bat` - Windows batch launcher
- `run_tests.py` - Test runner

### Core Logic
- `nba_api.py`, `models.py`, `statistics.py` - Statistical engine
- `database.py`, `cache_sqlite.py` - Data persistence
- `config.py`, `logger.py`, `error_handler.py` - Infrastructure

### Feature Modules
- `services/picks.py` - Pick of the Day service
- `components/*` - UI components
- `pages/pick_of_the_day.py` - Pick UI page

### Configuration
- `requirements.txt` - Python packages
- `pick_configs/picks.yaml` - Pick presets
- `.streamlit/config.toml` - App config
- `.streamlit/secrets.toml` - API keys

### Documentation
- `README.md` - Main readme (root)
- `docs/*` - All other documentation
- `attached_assets/nba-stats-mvp.md` - Complete specification

## ✨ Recent Changes (Oct 21, 2025)

### New Directories
- ✅ `services/` - Business logic layer
- ✅ `pick_configs/` - Pick configuration
- ✅ `data/` - Data files
- ✅ `docs/` - Consolidated documentation

### Organized Files
- ✅ All documentation → `docs/`
- ✅ Pick service → `services/`
- ✅ Pick page → `pages/`
- ✅ Schedule → `data/` (pending move)
- ✅ Pick config → `pick_configs/`

### Result
- **Before**: Scattered files in root
- **After**: Clean organization by purpose
- **Impact**: Easier navigation and maintenance

## 📝 Note

**Schedule CSV**: Currently in root (`nba_2025_2026_schedule.csv`)  
**Target**: `data/nba_2025_2026_schedule.csv`

**To move**: Stop app, run `move nba_2025_2026_schedule.csv data\`, restart app.  
Code already updated to look in `data/` folder.

