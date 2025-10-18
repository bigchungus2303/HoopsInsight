# HoopsInsight - Project Structure

**Clean, organized, production-ready structure**

**Last Updated:** October 18, 2025

---

## 📁 Directory Organization

```
HoopsInsight/
│
├── 🎯 Entry Points
│   ├── app.py                 # Main Streamlit application
│   ├── launch.py              # Cross-platform launcher
│   └── run_app.bat            # Windows batch launcher
│
├── 🧮 Core Modules (Business Logic)
│   ├── nba_api.py            # NBA API client with intelligent caching
│   ├── database.py           # SQLite database operations
│   ├── models.py             # Statistical models (Inverse-Frequency, Bayesian)
│   ├── statistics.py         # Statistical calculations and analysis
│   ├── config.py             # Centralized configuration
│   ├── logger.py             # Logging infrastructure
│   ├── error_handler.py      # Error handling utilities
│   └── export_utils.py       # Data export (CSV/JSON)
│
├── 🧩 UI Components (Reusable)
│   └── components/
│       ├── __init__.py
│       ├── api_dashboard.py     # API usage & cache stats
│       ├── advanced_settings.py # Threshold sliders & settings
│       ├── prediction_cards.py  # Prediction display widgets
│       ├── charts.py            # Reusable Plotly charts
│       └── lambda_advisor.py    # AI lambda recommendations
│
├── 📄 Pages (Application Views)
│   └── pages/
│       ├── __init__.py
│       ├── prediction_history.py  # Prediction tracking & accuracy
│       └── season_report.py       # Descriptive analysis
│
├── 🧪 Tests (Quality Assurance)
│   └── tests/
│       ├── __init__.py
│       ├── README.md
│       ├── test_models.py          # Model tests (13 tests)
│       ├── test_statistics.py      # Statistics tests (12 tests)
│       └── test_error_handling.py  # Error handling tests
│
├── 📚 Documentation
│   └── docs/
│       ├── IMPROVEMENTS.md               # Feature changelog
│       ├── TESTING.md                    # Testing guide
│       ├── DATABASE_ARCHITECTURE.md      # Database deep dive
│       ├── DATABASE_DIAGRAM.md           # Visual DB structure
│       ├── REFACTORING_SUMMARY.md        # Code organization
│       ├── PREDICTION_HISTORY_SUMMARY.md # Feature docs
│       ├── SEASON_REPORT_SUMMARY.md      # Feature docs
│       ├── LAMBDA_ADVISOR_UI.md          # AI advisor docs
│       ├── SEASON_REPORT_INDEPENDENCE.md # Architecture docs
│       ├── FIXES_APPLIED.md              # Bug fixes log
│       └── TROUBLESHOOTING_PAGES.md      # Debug guide
│
├── 📦 Assets
│   └── attached_assets/
│       ├── nba-stats-mvp.md     # Project specification
│       └── image_*.png          # Screenshots
│
├── ⚙️ Configuration
│   ├── .streamlit/
│   │   └── config.toml          # Streamlit settings
│   ├── .gitignore               # Git exclusions
│   ├── requirements.txt         # Python dependencies
│   └── pyproject.toml           # Project metadata
│
└── 💾 Data (Generated, Gitignored)
    └── nba_cache.db             # SQLite cache database
```

---

## 📊 File Count Summary

| Category | Files | Lines of Code |
|----------|-------|---------------|
| **Core Modules** | 8 | ~3500 |
| **UI Components** | 5 | ~650 |
| **Pages** | 2 | ~500 |
| **Tests** | 3 | ~800 |
| **Documentation** | 11 | ~3000 |
| **Entry Points** | 3 | ~150 |
| **Total** | **32** | **~8600** |

---

## 🎯 Module Dependencies

```
app.py (Entry Point)
├── imports Core Modules
│   ├── nba_api.py
│   ├── database.py
│   ├── models.py
│   ├── statistics.py
│   ├── config.py
│   ├── logger.py
│   ├── error_handler.py
│   └── export_utils.py
│
├── imports UI Components
│   ├── components.api_dashboard
│   ├── components.advanced_settings
│   ├── components.prediction_cards
│   ├── components.charts
│   └── components.lambda_advisor
│
└── imports Pages
    ├── pages.prediction_history
    └── pages.season_report
```

---

## 📝 File Purposes

### **Entry Points:**
- `app.py` - Main Streamlit app with routing (1000 lines)
- `launch.py` - Python launcher with error handling
- `run_app.bat` - Windows batch file for one-click start

### **Core Modules (Business Logic):**
- `nba_api.py` - API client, caching, rate limiting (400 lines)
- `database.py` - SQLite operations, 7 tables (725 lines)
- `models.py` - Inverse-frequency, Bayesian models (350 lines)
- `statistics.py` - Z-scores, career phase detection (300 lines)
- `config.py` - All constants and defaults (140 lines)
- `logger.py` - Centralized logging (55 lines)
- `error_handler.py` - Error handling utilities (245 lines)
- `export_utils.py` - CSV/JSON export (150 lines)

### **UI Components (Reusable Widgets):**
- `api_dashboard.py` - API usage statistics (50 lines)
- `advanced_settings.py` - Threshold sliders (150 lines)
- `prediction_cards.py` - Prediction display (60 lines)
- `charts.py` - Plotly chart functions (150 lines)
- `lambda_advisor.py` - AI recommendations (250 lines)

### **Pages (Application Views):**
- `prediction_history.py` - Track accuracy (230 lines)
- `season_report.py` - Descriptive analysis (280 lines)

### **Tests (Quality Assurance):**
- `test_models.py` - 13 model tests
- `test_statistics.py` - 12 statistics tests
- `test_error_handling.py` - Error handling tests

---

## 🎨 Design Principles

### **Separation of Concerns:**
```
Presentation Layer    → components/, pages/
Business Logic        → models.py, statistics.py, nba_api.py
Data Layer           → database.py
Configuration        → config.py
Cross-cutting        → logger.py, error_handler.py
```

### **Modularity:**
- Components are reusable across pages
- Pages are independent (own sidebars, own data)
- Core modules have single responsibilities
- Clear interfaces between layers

### **Maintainability:**
- Small, focused files (50-400 lines each)
- Comprehensive documentation
- Unit tests for critical logic
- Consistent code style

---

## 📂 What Goes Where?

### **Add New Feature:**
- New statistical model? → `models.py`
- New chart type? → `components/charts.py`
- New page? → Create in `pages/`
- New API endpoint? → `nba_api.py`

### **Add Documentation:**
- Feature summary? → `docs/`
- API changes? → Update `docs/DATABASE_ARCHITECTURE.md`
- User guide? → Update `README.md`

### **Add Test:**
- Model test? → `tests/test_models.py`
- Stats test? → `tests/test_statistics.py`
- New test file? → `tests/test_<module>.py`

---

## 🚀 Quick Navigation

### **For Developers:**
- Start here: `README.md`
- Code overview: This file (PROJECT_STRUCTURE.md)
- Database: `docs/DATABASE_ARCHITECTURE.md`
- Features: `docs/IMPROVEMENTS.md`
- Testing: `docs/TESTING.md`

### **For Users:**
- Getting started: `README.md`
- Troubleshooting: `docs/TROUBLESHOOTING_PAGES.md`
- Features: See app UI or `docs/IMPROVEMENTS.md`

---

## 🧹 Clean Repository Benefits

### **Before Cleanup:**
- 11 markdown files in root
- Hard to find documentation
- Cluttered root directory
- Unclear organization

### **After Cleanup:**
- Clean root with only essentials
- All docs in `docs/` folder
- Clear separation of concerns
- Professional structure

---

## 📊 File Organization Stats

**Root Directory:**
- Core files: 10
- Entry points: 3
- Config files: 3
- Folders: 6

**Total:** 16 items in root (down from 30+)

**Improvement:** 47% reduction in root clutter!

---

## ✅ Structure Follows Best Practices

1. ✅ **Separation of Concerns** - Modules, components, pages
2. ✅ **Documentation Centralized** - All in docs/
3. ✅ **Tests Organized** - All in tests/
4. ✅ **Clear Entry Points** - app.py, launch.py, run_app.bat
5. ✅ **Gitignore Proper** - Cache, env, pycache excluded
6. ✅ **No Temp Files** - All cleaned up

---

**The repository is now clean, organized, and professional!** 🎯

