# Database Architecture - Visual Diagram

## 🗄️ Complete Database Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NBA PERFORMANCE PREDICTOR                     │
│                         DATABASE ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          nba_cache.db (SQLite)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐                                               │
│  │    players       │  Player biographical info                     │
│  ├──────────────────┤                                               │
│  │ id (PK)          │  Cache expiry: 7 days                         │
│  │ first_name       │  Records: ~5-50 players                       │
│  │ last_name        │  Size: ~100 bytes/record                      │
│  │ team_id          │                                               │
│  │ team_name        │  Used by: Player search, display              │
│  │ position         │                                               │
│  │ height, weight   │                                               │
│  │ last_updated     │                                               │
│  └──────────────────┘                                               │
│         │                                                            │
│         │ player_id (FK relationship)                               │
│         ├────────────────────────────────────┐                      │
│         │                                    │                      │
│         ↓                                    ↓                      │
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │  season_stats    │              │   game_stats     │            │
│  ├──────────────────┤              ├──────────────────┤            │
│  │ id (PK)          │              │ id (PK)          │            │
│  │ player_id (FK)   │              │ player_id (FK)   │            │
│  │ season           │              │ game_id          │            │
│  │ postseason       │              │ game_date        │            │
│  │ games_played     │              │ season           │            │
│  │ pts, reb, ast    │              │ postseason       │            │
│  │ fg%, 3p%, ft%    │              │ pts, reb, ast    │            │
│  │ min              │              │ fg%, 3pm, min    │            │
│  │ last_updated     │              │ last_updated     │            │
│  │                  │              │                  │            │
│  │ UNIQUE(player,   │              │ UNIQUE(player,   │            │
│  │  season, post)   │              │  game_id)        │            │
│  └──────────────────┘              └──────────────────┘            │
│   Cache: 1 day                      Cache: 1 day                   │
│   Records: ~100                     Records: ~2000 games           │
│   Per-game averages                 Individual game stats          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────┐          │
│  │            league_averages                           │          │
│  ├──────────────────────────────────────────────────────┤          │
│  │ season (PK)                                          │          │
│  │ pts, reb, ast (means)                                │          │
│  │ pts_std, reb_std, ast_std (std devs)                │          │
│  │ fg%, 3p%, ft% (means + std devs)                    │          │
│  │ last_updated                                         │          │
│  └──────────────────────────────────────────────────────┘          │
│   Cache: 7 days                                                    │
│   Records: ~5 seasons                                              │
│   For z-score normalization                                        │
│                                                                     │
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │   favorites      │              │   predictions    │            │
│  ├──────────────────┤              ├──────────────────┤            │
│  │ id (PK)          │              │ id (PK)          │            │
│  │ player_id (UQ)   │              │ player_id (FK)   │            │
│  │ player_name      │              │ player_name      │            │
│  │ added_date       │              │ game_date        │            │
│  └──────────────────┘              │ season           │            │
│   No expiry                         │ stat_type        │            │
│   User preferences                  │ threshold        │            │
│                                     │ predicted_prob   │            │
│                                     │ confidence       │            │
│                                     │ actual_result    │            │
│                                     │ actual_value     │            │
│                                     │ prediction_correct│           │
│                                     │ created_at       │            │
│                                     │ verified_at      │            │
│                                     └──────────────────┘            │
│                                      No expiry                      │
│                                      Historical record              │
│                                            │                        │
│                                            │ Aggregates into        │
│                                            ↓                        │
│                                     ┌──────────────────┐            │
│                                     │prediction_metrics│            │
│                                     ├──────────────────┤            │
│                                     │ id (PK)          │            │
│                                     │ stat_type        │            │
│                                     │ threshold_range  │            │
│                                     │ total_predictions│            │
│                                     │ correct_pred     │            │
│                                     │ accuracy_rate    │            │
│                                     │ last_updated     │            │
│                                     │                  │            │
│                                     │ UNIQUE(stat,range)│           │
│                                     └──────────────────┘            │
│                                      Auto-updated                   │
│                                      Aggregate stats                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow: User Loads Player

```
┌─────────────┐
│   User      │ "Load LeBron James"
└──────┬──────┘
       ↓
┌──────────────────────────────────────────────────────┐
│  app.py                                              │
│  api_client.get_season_stats(237, 2024)             │
└──────┬───────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────┐
│  nba_api.py                                          │
│  1. Check database first                             │
│     db.get_season_stats(237, 2024)                  │
└──────┬───────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────┐
│  database.py                                         │
│  SELECT * FROM season_stats                          │
│  WHERE player_id=237 AND season=2024                │
└──────┬───────────────────────────────────────────────┘
       ↓
       ├─── Cache Hit (found, < 1 day old)
       │    └─→ Return cached data
       │        cache_hit_count++
       │
       └─── Cache Miss (not found or expired)
            ↓
       ┌──────────────────────────────────┐
       │  nba_api.py                      │
       │  2. Make API request              │
       │     GET balldontlie.io/v1/stats  │
       │     api_call_count++              │
       └──────┬───────────────────────────┘
              ↓
       ┌──────────────────────────────────┐
       │  database.py                      │
       │  3. Cache response                │
       │     INSERT INTO season_stats      │
       │     VALUES (237, 2024, ...)      │
       └──────┬───────────────────────────┘
              ↓
         Return data to app
```

---

## 🎯 Prediction Tracking Flow

```
Step 1: Save Prediction
┌────────────────────────────────────────┐
│ User clicks "Save Prediction"          │
│ LeBron ≥20 pts, 65% probability       │
└────────┬───────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ database.save_prediction(                           │
│   player_id=237,                                    │
│   player_name="LeBron James",                       │
│   game_date="2025-01-15",                          │
│   threshold=20.0,                                   │
│   predicted_probability=0.65,                       │
│   confidence="High"                                 │
│ )                                                   │
└────────┬────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ INSERT INTO predictions (...)                       │
│ VALUES (237, "LeBron", "2025-01-15", "pts", 20, ...) │
│                                                      │
│ actual_result = NULL  (not verified yet)           │
│ verified_at = NULL                                  │
└────────┬────────────────────────────────────────────┘
         ↓
    Returns prediction_id = 42

Step 2: Verify Prediction (After Game)
┌────────────────────────────────────────┐
│ User enters actual result: 28 points   │
└────────┬───────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ database.verify_prediction(                         │
│   prediction_id=42,                                 │
│   actual_value=28.0                                │
│ )                                                   │
└────────┬────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ 1. Get prediction details (threshold=20)            │
│ 2. Calculate:                                       │
│    actual_result = 1 (28 >= 20)                    │
│    prediction_correct = 1 (predicted>0.5 and true) │
│ 3. UPDATE predictions SET                           │
│    actual_value=28, actual_result=1,               │
│    prediction_correct=1, verified_at=NOW           │
└────────┬────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ 4. Update aggregate metrics                         │
│    _update_prediction_metrics("pts", 20, correct=1) │
│                                                      │
│    UPDATE prediction_metrics SET                    │
│    total_predictions = total + 1                    │
│    correct_predictions = correct + 1                │
│    accuracy_rate = (correct/total)*100             │
│    WHERE stat_type='pts' AND threshold_range='high'│
└─────────────────────────────────────────────────────┘
```

---

## 📊 Cache Hit Rate Calculation

```
Session Start:
api_call_count = 0
cache_hit_count = 0

User loads LeBron:
├─ get_season_stats() → Cache MISS → API call
│  api_call_count = 1
├─ get_recent_games() → Cache MISS → API call  
│  api_call_count = 2
└─ get_career_stats() → Cache MISS → API call
   api_call_count = 3

User reloads LeBron:
├─ get_season_stats() → Cache HIT ✓
│  cache_hit_count = 1
├─ get_recent_games() → Cache HIT ✓
│  cache_hit_count = 2
└─ get_career_stats() → Cache HIT ✓
   cache_hit_count = 3

Results:
total_requests = 6
cache_hit_rate = (3/6) * 100 = 50%
```

---

## 🎨 ERD (Entity Relationship Diagram)

```
┌─────────────┐
│   players   │────┐
└─────────────┘    │ 1:N
      ↑            ↓
      │      ┌─────────────────┐
      │      │  season_stats   │
      │      └─────────────────┘
      │
      │      ┌─────────────────┐
      ├──────│   game_stats    │
      │      └─────────────────┘
      │
      │      ┌─────────────────┐
      ├──────│   favorites     │
      │      └─────────────────┘
      │
      │      ┌─────────────────┐
      └──────│  predictions    │────┐
             └─────────────────┘    │ aggregates
                                    │ into
                                    ↓
                          ┌──────────────────────┐
                          │ prediction_metrics   │
                          └──────────────────────┘

┌─────────────────────┐
│  league_averages    │  Independent (no FK)
└─────────────────────┘
```

---

## 🔍 SQL Examples

### **Cache a Player:**
```sql
INSERT OR REPLACE INTO players 
(id, first_name, last_name, team_name, team_abbreviation, position, last_updated)
VALUES (237, 'LeBron', 'James', 'Los Angeles Lakers', 'LAL', 'F', CURRENT_TIMESTAMP);
```

### **Get Cached Season Stats:**
```sql
SELECT * FROM season_stats
WHERE player_id = 237 
  AND season = 2024
  AND postseason = 0
  AND datetime(last_updated) > datetime('now', '-1 day');
```

### **Get Recent Games (Cached):**
```sql
SELECT * FROM game_stats
WHERE player_id = 237
  AND season = 2024
  AND postseason = 0
ORDER BY game_date DESC
LIMIT 20;
```

### **Track Prediction Accuracy:**
```sql
-- Save prediction
INSERT INTO predictions 
(player_id, player_name, game_date, stat_type, threshold, predicted_probability, prediction_confidence)
VALUES (237, 'LeBron James', '2025-01-15', 'pts', 20.0, 0.65, 'High');

-- Verify prediction
UPDATE predictions 
SET actual_value = 28.0,
    actual_result = 1,
    prediction_correct = 1,
    verified_at = CURRENT_TIMESTAMP
WHERE id = 42;

-- Get accuracy
SELECT stat_type, threshold_range, accuracy_rate, total_predictions
FROM prediction_metrics
WHERE total_predictions > 0
ORDER BY accuracy_rate DESC;
```

---

**This comprehensive documentation shows the complete database architecture, data flows, and how everything interacts!** 🗄️📊

