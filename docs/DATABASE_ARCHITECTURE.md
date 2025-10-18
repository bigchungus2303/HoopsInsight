# NBA Performance Predictor - Database Architecture

**Complete Documentation of Database Design and Data Flow**

**Last Updated:** October 18, 2025

---

## 📊 Database Overview

### **Technology**
- **Engine:** SQLite 3
- **File:** `nba_cache.db`
- **Location:** Project root directory
- **Size:** ~50-500 KB (depends on cache)
- **Purpose:** Caching API responses, user preferences, prediction tracking

### **Design Philosophy**
1. **Reduce API Calls:** Cache all API responses with expiry
2. **Improve Performance:** Instant data retrieval from cache
3. **Track User Data:** Favorites and prediction history
4. **Enable Analytics:** Store predictions for model validation

---

## 🗄️ Database Schema

### **7 Tables Total:**

```
nba_cache.db
├── players              (Player info cache)
├── season_stats         (Season averages cache)
├── game_stats           (Individual games cache)
├── league_averages      (League-wide stats cache)
├── favorites            (User's favorite players)
├── predictions          (Saved predictions for tracking)
└── prediction_metrics   (Aggregate accuracy metrics)
```

---

## 📋 Table Schemas

### **1. players**
**Purpose:** Cache player biographical information

```sql
CREATE TABLE players (
    id INTEGER PRIMARY KEY,              -- NBA API player ID
    first_name TEXT,                     -- "LeBron"
    last_name TEXT,                      -- "James"
    team_id INTEGER,                     -- Current team ID
    team_name TEXT,                      -- "Los Angeles Lakers"
    team_abbreviation TEXT,              -- "LAL"
    position TEXT,                       -- "F" or "G-F"
    height_feet INTEGER,                 -- 6
    height_inches INTEGER,               -- 9
    weight_pounds INTEGER,               -- 250
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:** Primary key on `id` (player ID)

**Cache Expiry:** 7 days (players rarely change teams mid-season)

**Used By:**
- `nba_api.py` - Stores player search results
- `app.py` - Displays player info

---

### **2. season_stats**
**Purpose:** Cache season averages (per-game stats)

```sql
CREATE TABLE season_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,                   -- FK to players.id
    season INTEGER,                      -- 2024 (for 2024-25 season)
    postseason INTEGER DEFAULT 0,        -- 0=Regular, 1=Playoffs
    games_played INTEGER,                -- Number of games
    pts REAL,                            -- Points per game
    reb REAL,                            -- Rebounds per game
    ast REAL,                            -- Assists per game
    fg_pct REAL,                         -- Field goal %
    fg3_pct REAL,                        -- 3-point %
    ft_pct REAL,                         -- Free throw %
    min REAL,                            -- Minutes per game
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season, postseason) -- One record per player/season/type
)
```

**Indexes:** 
- Primary key on `id`
- Unique constraint on `(player_id, season, postseason)`

**Cache Expiry:** 1 day (season stats update frequently)

**Used By:**
- `nba_api.get_season_stats()` - Fetches and caches
- `statistics.py` - Calculates z-scores
- `app.py` - Displays season averages

---

### **3. game_stats**
**Purpose:** Cache individual game statistics

```sql
CREATE TABLE game_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,                   -- FK to players.id
    game_id INTEGER,                     -- Unique game ID from API
    game_date TEXT,                      -- "2024-10-23"
    season INTEGER,                      -- 2024
    postseason INTEGER DEFAULT 0,        -- 0=Regular, 1=Playoffs
    pts REAL,                            -- Points scored
    reb REAL,                            -- Total rebounds
    ast REAL,                            -- Assists
    fg_pct REAL,                         -- FG% for game
    fg3m REAL,                           -- 3-pointers made
    min REAL,                            -- Minutes played
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, game_id)           -- One record per player per game
)
```

**Indexes:**
- Primary key on `id`
- Unique constraint on `(player_id, game_id)`

**Cache Expiry:** 1 day

**Used By:**
- `nba_api.get_recent_games()` - Fetches and caches
- `models.py` - Calculates probabilities
- `pages/season_report.py` - Descriptive analysis

---

### **4. league_averages**
**Purpose:** Cache league-wide averages for z-score calculations

```sql
CREATE TABLE league_averages (
    season INTEGER PRIMARY KEY,          -- 2024
    pts REAL,                            -- League avg PPG
    reb REAL,                            -- League avg RPG
    ast REAL,                            -- League avg APG
    fg_pct REAL,                         -- League avg FG%
    fg3_pct REAL,                        -- League avg 3P%
    ft_pct REAL,                         -- League avg FT%
    min REAL,                            -- League avg MPG
    pts_std REAL,                        -- Std deviation for PTS
    reb_std REAL,                        -- Std deviation for REB
    ast_std REAL,                        -- Std deviation for AST
    fg_pct_std REAL,                     -- Std deviation for FG%
    fg3_pct_std REAL,                    -- Std deviation for 3P%
    ft_pct_std REAL,                     -- Std deviation for FT%
    min_std REAL,                        -- Std deviation for MIN
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:** Primary key on `season`

**Cache Expiry:** 7 days (league averages stable)

**Used By:**
- `statistics.calculate_z_scores()` - Normalizes player stats
- `nba_api.get_league_averages()` - Fetches and caches
- `app.py` - Z-score displays

---

### **5. favorites**
**Purpose:** Store user's favorite players for quick access

```sql
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER UNIQUE,            -- FK to players.id
    player_name TEXT,                    -- "LeBron James"
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- Primary key on `id`
- Unique constraint on `player_id`

**Cache Expiry:** None (user data persists)

**Used By:**
- `database.add_favorite()` - Add player
- `database.remove_favorite()` - Remove player
- `database.get_favorites()` - List all favorites
- `app.py` - Favorites quick access in sidebar

---

### **6. predictions**
**Purpose:** Track predictions for model validation

```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,                   -- FK to players.id
    player_name TEXT,                    -- "LeBron James"
    game_date DATE,                      -- "2025-01-15"
    season INTEGER,                      -- 2024
    stat_type TEXT,                      -- "pts", "reb", "ast", "fg3m"
    threshold REAL,                      -- 20.0
    predicted_probability REAL,          -- 0.65 (65% probability)
    prediction_confidence TEXT,          -- "High" or "Low"
    actual_result INTEGER,               -- 1=achieved, 0=missed, NULL=unverified
    actual_value REAL,                   -- 28.0 (actual points scored)
    prediction_correct INTEGER,          -- 1=correct, 0=incorrect, NULL=unverified
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP                -- NULL until verified
)
```

**Indexes:** Primary key on `id`

**Cache Expiry:** None (permanent record)

**Used By:**
- `database.save_prediction()` - Save new prediction
- `database.verify_prediction()` - Verify after game
- `database.get_recent_predictions()` - List predictions
- `database.get_unverified_predictions()` - Pending verifications
- `pages/prediction_history.py` - Display and verify

---

### **7. prediction_metrics**
**Purpose:** Aggregate prediction accuracy statistics

```sql
CREATE TABLE prediction_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_type TEXT,                      -- "pts", "reb", "ast", "fg3m"
    threshold_range TEXT,                -- "low", "medium", "high"
    total_predictions INTEGER DEFAULT 0,  -- Total predictions made
    correct_predictions INTEGER DEFAULT 0,-- Number correct
    accuracy_rate REAL DEFAULT 0.0,      -- Percentage (0-100)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_type, threshold_range)   -- One record per stat/range combo
)
```

**Threshold Ranges:**
- **low:** threshold < 10
- **medium:** 10 ≤ threshold < 20
- **high:** threshold ≥ 20

**Indexes:**
- Primary key on `id`
- Unique constraint on `(stat_type, threshold_range)`

**Cache Expiry:** None (aggregate stats)

**Used By:**
- `database._update_prediction_metrics()` - Auto-updates on verification
- `database.get_prediction_accuracy()` - Retrieve accuracy stats
- `pages/prediction_history.py` - Accuracy dashboard

---

## 🔄 Data Flow Architecture

### **Request Flow: Get Player Stats**

```
User Action (Load Player)
    ↓
app.py calls api_client.get_season_stats(player_id, season)
    ↓
nba_api.py checks database.get_season_stats(player_id, season)
    ↓
┌─── Cache Hit (data exists, < 1 day old) ───┐
│   Return cached data immediately           │
│   (No API call made)                       │
│   cache_hit_count += 1                     │
└────────────────────────────────────────────┘
    OR
┌─── Cache Miss (no data or expired) ────────┐
│   Make API request to balldontlie.io       │
│   api_call_count += 1                      │
│   Parse response                           │
│   database.cache_season_stats(data)        │
│   Return data                              │
└────────────────────────────────────────────┘
    ↓
Data returned to app.py
    ↓
Display in UI
```

---

### **Prediction Workflow**

```
1. User Views Predictions
   ↓
app.py → models.calculate_inverse_frequency_probabilities()
   ↓
Returns probability results

2. User Saves Prediction
   ↓
app.py → database.save_prediction(player_id, threshold, probability, ...)
   ↓
INSERT INTO predictions table
   ↓
prediction_id returned

3. After Game is Played
   ↓
User goes to Prediction History
   ↓
pages/prediction_history.py → database.get_unverified_predictions()
   ↓
SELECT * FROM predictions WHERE verified_at IS NULL

4. User Verifies Result
   ↓
database.verify_prediction(prediction_id, actual_value)
   ↓
┌─ UPDATE predictions SET actual_value, prediction_correct, verified_at
├─ Calculate if prediction was correct
└─ database._update_prediction_metrics() updates aggregate stats
   ↓
UPDATE prediction_metrics SET total_predictions++, correct_predictions++, accuracy_rate
```

---

## 🔗 Module Interactions

### **Who Uses the Database?**

```
database.py (NBADatabase class)
    ↑
    ├── nba_api.py (NBAAPIClient)
    │   └── Cache all API responses
    │
    ├── app.py (Main application)
    │   ├── Favorites management
    │   └── Save predictions
    │
    ├── pages/prediction_history.py
    │   ├── Get predictions
    │   ├── Verify predictions
    │   └── Get accuracy metrics
    │
    └── pages/season_report.py
        └── Uses cached game data (via api_client)
```

---

## 📈 Data Lifecycle

### **Player Data:**

```
Search → API → Cache → Display → Expire (7 days) → Re-fetch

Timeline:
Day 0:  API call, store in players table
Day 1-7: Serve from cache (instant)
Day 8+: Cache expired, API call again, refresh cache
```

### **Season Stats:**

```
Request → Check cache → API (if expired) → Display

Timeline:
Hour 0:  API call, store in season_stats table
Hour 1-24: Serve from cache
Hour 24+: Cache expired, API call, refresh
```

### **Game Stats:**

```
Request recent games → Check cache → API (if expired) → Display

Cache Strategy:
- Stores individual games with UNIQUE(player_id, game_id)
- Checks if cached_games >= requested_limit
- If enough cached games, returns from cache
- Otherwise, fetches fresh from API
```

### **Predictions:**

```
Save → Store → Wait for game → Verify → Update metrics

Timeline:
T0:  User saves prediction → INSERT INTO predictions
T1:  Game is played (external event)
T2:  User verifies → UPDATE predictions, UPDATE prediction_metrics
T3:  Metrics displayed in dashboard
```

---

## 🔍 Cache Invalidation Strategy

| Table | Expiry | Strategy | Reason |
|-------|--------|----------|--------|
| **players** | 7 days | Time-based | Player info rarely changes |
| **season_stats** | 1 day | Time-based | Stats update daily |
| **game_stats** | 1 day | Time-based | Recent games update daily |
| **league_averages** | 7 days | Time-based | League averages stable |
| **favorites** | Never | User-controlled | User preference |
| **predictions** | Never | Permanent | Historical record |
| **prediction_metrics** | Never | Auto-updates | Aggregate stats |

**Cache Check:**
```python
if last_updated > (now - expiry_days):
    return cached_data  # Valid
else:
    fetch_fresh_data()  # Expired
```

---

## 🔄 Database Methods

### **Connection Management**

```python
@contextmanager
def _get_connection(self):
    """Context manager for database connections"""
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row  # Dict-like access
    try:
        yield conn
    finally:
        conn.close()
```

**Usage:**
```python
with self._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    results = cursor.fetchall()
```

---

### **Player Methods**

| Method | Purpose | Returns |
|--------|---------|---------|
| `cache_player(player)` | Store player info | None |
| `get_player(player_id)` | Retrieve cached player | Dict or None |

---

### **Season Stats Methods**

| Method | Purpose | Returns |
|--------|---------|---------|
| `cache_season_stats(player_id, season, stats, postseason)` | Store season averages | None |
| `get_season_stats(player_id, season, postseason)` | Retrieve cached stats | Dict or None |

---

### **Game Stats Methods**

| Method | Purpose | Returns |
|--------|---------|---------|
| `cache_game_stats(player_id, games)` | Store multiple games | None |
| `get_game_stats(player_id, limit, season, postseason)` | Retrieve cached games | List[Dict] |

**Special Logic:**
- Checks if cached games >= requested limit
- Filters by season and postseason type
- Orders by date descending (most recent first)

---

### **League Averages Methods**

| Method | Purpose | Returns |
|--------|---------|---------|
| `cache_league_averages(season, averages)` | Store league stats | None |
| `get_league_averages(season)` | Retrieve league averages | Dict or None |

---

### **Favorites Methods**

| Method | Purpose | Returns |
|--------|---------|---------|
| `add_favorite(player_id, player_name)` | Add to favorites | None |
| `remove_favorite(player_id)` | Remove from favorites | None |
| `get_favorites()` | List all favorites | List[Dict] |
| `is_favorite(player_id)` | Check if favorited | Bool |

**Unique Constraint:** Can't favorite same player twice

---

### **Prediction Tracking Methods**

| Method | Purpose | Returns |
|--------|---------|---------|
| `save_prediction(...)` | Save new prediction | Int (prediction_id) |
| `verify_prediction(prediction_id, actual_value)` | Verify after game | Bool |
| `get_recent_predictions(player_id, limit, verified_only)` | List predictions | List[Dict] |
| `get_unverified_predictions(cutoff_date)` | Get pending verifications | List[Dict] |
| `get_prediction_accuracy(stat_type)` | Get accuracy metrics | List[Dict] |
| `_update_prediction_metrics(...)` | Update aggregate stats | None (internal) |

---

## 📊 Query Patterns

### **Pattern 1: Try Cache First**
```python
# Check cache
cached_data = db.get_season_stats(player_id, season)

if cached_data:
    cache_hit_count += 1
    return cached_data  # Fast path
else:
    # Fetch from API
    data = api.fetch()
    db.cache_season_stats(data)
    api_call_count += 1
    return data
```

### **Pattern 2: Conditional Filtering**
```python
query = "SELECT * FROM predictions WHERE 1=1"
params = []

if player_id:
    query += " AND player_id = ?"
    params.append(player_id)

if verified_only:
    query += " AND verified_at IS NOT NULL"

cursor.execute(query, params)
```

### **Pattern 3: Aggregate Updates**
```python
# Atomic update with transaction
with conn:
    cursor.execute("SELECT total, correct FROM metrics")
    row = cursor.fetchone()
    
    new_total = row['total'] + 1
    new_correct = row['correct'] + (1 if correct else 0)
    new_accuracy = (new_correct / new_total) * 100
    
    cursor.execute("""
        UPDATE metrics 
        SET total = ?, correct = ?, accuracy = ?
    """, (new_total, new_correct, new_accuracy))
```

---

## 🎯 Data Relationships

```
players (1) ─────┬──── (N) season_stats
                 ├──── (N) game_stats
                 ├──── (1) favorites
                 └──── (N) predictions

predictions (N) ─────── (1) prediction_metrics (aggregated)
                         (grouped by stat_type + threshold_range)
```

**Relationships:**
- One player → Many season stats (one per season/type)
- One player → Many games
- One player → One favorite entry (or none)
- One player → Many predictions

---

## 📦 Storage Estimates

### **Typical Database Sizes:**

| Usage Level | Size | Records |
|-------------|------|---------|
| **Fresh install** | ~50 KB | Empty tables |
| **Light use (5 players)** | ~200 KB | 5 players, 100 games, 10 predictions |
| **Medium use (20 players)** | ~500 KB | 20 players, 400 games, 50 predictions |
| **Heavy use (50+ players)** | ~2 MB | 50+ players, 1000+ games, 200+ predictions |

**Calculation:**
- Player record: ~100 bytes
- Season stats: ~80 bytes
- Game stats: ~60 bytes
- Prediction: ~120 bytes

---

## 🔐 Data Integrity

### **Constraints:**

1. **UNIQUE Constraints:**
   - `season_stats(player_id, season, postseason)` - No duplicates
   - `game_stats(player_id, game_id)` - No duplicate games
   - `favorites(player_id)` - Can't favorite twice
   - `prediction_metrics(stat_type, threshold_range)` - One record per combo

2. **Foreign Key Behavior:**
   - No explicit FK constraints (SQLite limitation)
   - Logical relationships maintained by application

3. **NULL Handling:**
   - `predictions.actual_value` - NULL until verified
   - `predictions.verified_at` - NULL until verified
   - `league_averages` fields - Never NULL

---

## 🚀 Performance Optimizations

### **1. Connection Pooling**
```python
# Single connection per transaction
with self._get_connection() as conn:
    # Multiple operations share connection
    cursor.execute(...)
    cursor.execute(...)
    conn.commit()
```

### **2. Batch Inserts**
```python
def cache_game_stats(self, player_id, games):
    # Insert multiple games in one transaction
    cursor.executemany("""
        INSERT OR REPLACE INTO game_stats (...)
        VALUES (?, ?, ...)
    """, game_data)
```

### **3. Indexed Lookups**
- Primary keys for fast ID lookups
- UNIQUE constraints create implicit indexes
- Date-based queries benefit from chronological data

### **4. Row Factory**
```python
conn.row_factory = sqlite3.Row
# Allows dict-like access: row['player_name']
# Instead of tuple access: row[0]
```

---

## 🛠️ Maintenance Operations

### **Reset Cache:**
```python
# Clear expired cache (manual)
DELETE FROM season_stats 
WHERE last_updated < datetime('now', '-1 day')
```

### **View Cache Status:**
```sql
SELECT 
    'players' as table_name, COUNT(*) as records 
FROM players
UNION ALL
SELECT 'season_stats', COUNT(*) FROM season_stats
UNION ALL
SELECT 'game_stats', COUNT(*) FROM game_stats
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions;
```

### **Database Size:**
```python
import os
size_bytes = os.path.getsize('nba_cache.db')
size_mb = size_bytes / (1024 * 1024)
```

---

## 🔍 Example Queries

### **Get Player's All-Time Stats:**
```sql
SELECT season, pts, reb, ast
FROM season_stats
WHERE player_id = 237  -- LeBron James
  AND postseason = 0
ORDER BY season DESC
```

### **Get Recent Hot Streak:**
```sql
SELECT game_date, pts
FROM game_stats  
WHERE player_id = 237
  AND pts > 30
ORDER BY game_date DESC
LIMIT 5
```

### **Get Prediction Accuracy:**
```sql
SELECT 
    stat_type,
    threshold_range,
    accuracy_rate,
    total_predictions
FROM prediction_metrics
WHERE total_predictions >= 10
ORDER BY accuracy_rate DESC
```

---

## 📝 Database Initialization

**Automatic on First Run:**

```python
# On app startup
db = NBADatabase()  # Creates nba_cache.db if doesn't exist
    ↓
_init_database() called
    ↓
CREATE TABLE IF NOT EXISTS ... (all 7 tables)
    ↓
Migrations applied (if schema changed)
    ↓
Ready to use
```

**Location:** `nba_cache.db` in project root

**Backup:** Simply copy `nba_cache.db` file

---

## 🎯 Cache Effectiveness

### **Metrics Tracked:**

```python
api_client.get_cache_stats()
→ {
    'api_calls': 15,        # Actual API requests
    'cache_hits': 45,       # Cache retrievals
    'total_requests': 60,   # Total
    'cache_hit_rate': 75.0  # 75% from cache!
}
```

**Good Cache Performance:**
- 70%+ hit rate = Excellent (most data from cache)
- 40-70% hit rate = Good (balanced)
- <40% hit rate = Low (many API calls)

---

## 🔄 Migration System

### **Built-in Migration:**

```python
# Check if old schema
if 'postseason' not in season_stats_columns:
    # Create new table
    CREATE TABLE season_stats_new (...)
    
    # Copy data
    INSERT INTO season_stats_new 
    SELECT * FROM season_stats
    
    # Swap tables
    DROP TABLE season_stats
    ALTER TABLE season_stats_new RENAME TO season_stats
```

**Runs automatically on startup - no user action needed!**

---

## 📊 Summary

### **Database Serves 4 Purposes:**

1. **Performance** (Caching)
   - 75%+ requests served from cache
   - Instant data retrieval
   - Reduced API rate limiting

2. **User Preferences** (Favorites)
   - Quick access to frequently viewed players
   - Persists across sessions

3. **Model Validation** (Predictions)
   - Track prediction accuracy
   - Build historical record
   - Validate statistical models

4. **Analytics** (Metrics)
   - Aggregate statistics
   - Performance trends
   - Accuracy tracking

---

**The database is a critical component that enables fast, responsive performance while tracking user preferences and model accuracy over time!** 🗄️

---

**Files:** 
- Database implementation: `database.py` (726 lines)
- Physical database: `nba_cache.db` (SQLite file)
- Configuration: `config.py` (cache expiry settings)

