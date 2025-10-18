import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from contextlib import contextmanager


class NBADatabase:
    """SQLite database for caching NBA player data and reducing API calls"""

    def __init__(self, db_path: str = "nba_cache.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Players table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    team_id INTEGER,
                    team_name TEXT,
                    team_abbreviation TEXT,
                    position TEXT,
                    height_feet INTEGER,
                    height_inches INTEGER,
                    weight_pounds INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Season stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS season_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    season INTEGER,
                    postseason INTEGER DEFAULT 0,
                    games_played INTEGER,
                    pts REAL,
                    reb REAL,
                    ast REAL,
                    fg_pct REAL,
                    fg3_pct REAL,
                    ft_pct REAL,
                    min REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(player_id, season, postseason)
                )
            """)

            # Game stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    game_id INTEGER,
                    game_date TEXT,
                    season INTEGER,
                    postseason INTEGER DEFAULT 0,
                    pts REAL,
                    reb REAL,
                    ast REAL,
                    fg_pct REAL,
                    fg3m REAL,
                    min REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(player_id, game_id)
                )
            """)

            # League averages cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS league_averages (
                    season INTEGER PRIMARY KEY,
                    pts REAL,
                    reb REAL,
                    ast REAL,
                    fg_pct REAL,
                    fg3_pct REAL,
                    ft_pct REAL,
                    min REAL,
                    pts_std REAL,
                    reb_std REAL,
                    ast_std REAL,
                    fg_pct_std REAL,
                    fg3_pct_std REAL,
                    ft_pct_std REAL,
                    min_std REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User favorites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER UNIQUE,
                    player_name TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Predictions tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    player_name TEXT,
                    game_date DATE,
                    season INTEGER,
                    stat_type TEXT,
                    threshold REAL,
                    predicted_probability REAL,
                    prediction_confidence TEXT,
                    actual_result INTEGER,
                    actual_value REAL,
                    prediction_correct INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP
                )
            """)
            
            # Prediction accuracy metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prediction_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_type TEXT,
                    threshold_range TEXT,
                    total_predictions INTEGER DEFAULT 0,
                    correct_predictions INTEGER DEFAULT 0,
                    accuracy_rate REAL DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stat_type, threshold_range)
                )
            """)

            # Migration: Rebuild season_stats table with correct UNIQUE constraint
            cursor.execute("PRAGMA table_info(season_stats)")
            season_stats_columns = [col[1] for col in cursor.fetchall()]
            if 'postseason' not in season_stats_columns:
                # Create temp table with new schema
                cursor.execute("""
                    CREATE TABLE season_stats_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id INTEGER,
                        season INTEGER,
                        postseason INTEGER DEFAULT 0,
                        games_played INTEGER,
                        pts REAL,
                        reb REAL,
                        ast REAL,
                        fg_pct REAL,
                        fg3_pct REAL,
                        ft_pct REAL,
                        min REAL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(player_id, season, postseason)
                    )
                """)
                # Copy existing data (all regular season, postseason=0)
                cursor.execute("""
                    INSERT INTO season_stats_new (id, player_id, season, postseason, games_played, 
                                                   pts, reb, ast, fg_pct, fg3_pct, ft_pct, min, last_updated)
                    SELECT id, player_id, season, 0, games_played, pts, reb, ast, 
                           fg_pct, fg3_pct, ft_pct, min, last_updated
                    FROM season_stats
                """)
                # Drop old table and rename new one
                cursor.execute("DROP TABLE season_stats")
                cursor.execute("ALTER TABLE season_stats_new RENAME TO season_stats")
            
            # Migration: Rebuild game_stats table with correct UNIQUE constraint
            cursor.execute("PRAGMA table_info(game_stats)")
            game_stats_columns = [col[1] for col in cursor.fetchall()]
            if 'postseason' not in game_stats_columns:
                cursor.execute("ALTER TABLE game_stats ADD COLUMN postseason INTEGER DEFAULT 0")

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def cache_player(self, player_data: Dict):
        """Cache player information"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO players 
                (id, first_name, last_name, team_id, team_name, team_abbreviation,
                 position, height_feet, height_inches, weight_pounds, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (player_data['id'], player_data.get('first_name'),
                  player_data.get('last_name'), player_data.get(
                      'team', {}).get('id'), player_data.get(
                          'team', {}).get('full_name'),
                  player_data.get('team', {}).get('abbreviation'),
                  player_data.get('position'), player_data.get('height_feet'),
                  player_data.get('height_inches'),
                  player_data.get('weight_pounds')))

            conn.commit()

    def get_player(self, player_id: int) -> Optional[Dict]:
        """Retrieve cached player data"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM players 
                WHERE id = ? AND last_updated > datetime('now', '-7 days')
            """, (player_id, ))

            row = cursor.fetchone()

            if row:
                return {
                    'id': row['id'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'team': {
                        'id': row['team_id'],
                        'full_name': row['team_name'],
                        'abbreviation': row['team_abbreviation']
                    },
                    'position': row['position'],
                    'height_feet': row['height_feet'],
                    'height_inches': row['height_inches'],
                    'weight_pounds': row['weight_pounds']
                }

            return None

    def search_cached_players(self, query: str) -> List[Dict]:
        """Search for players in cache"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            search_pattern = f"%{query}%"
            cursor.execute(
                """
                SELECT * FROM players 
                WHERE (first_name LIKE ? OR last_name LIKE ?)
                AND last_updated > datetime('now', '-7 days')
                LIMIT 10
            """, (search_pattern, search_pattern))

            rows = cursor.fetchall()

            return [self._player_row_to_dict(row) for row in rows]

    def cache_season_stats(self, player_id: int, season: int, stats: Dict, postseason: bool = False):
        """Cache season statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO season_stats
                (player_id, season, postseason, games_played, pts, reb, ast, 
                 fg_pct, fg3_pct, ft_pct, min, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (player_id,
                  season, 1 if postseason else 0, stats.get('games_played'), stats.get('pts'),
                  stats.get('reb'), stats.get('ast'), stats.get('fg_pct'),
                  stats.get('fg3_pct'), stats.get('ft_pct'), stats.get('min')))

            conn.commit()

    def get_season_stats(self, player_id: int, season: int, postseason: bool = False) -> Optional[Dict]:
        """Retrieve cached season stats"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM season_stats 
                WHERE player_id = ? AND season = ? AND postseason = ?
                AND last_updated > datetime('now', '-1 day')
            """, (player_id, season, 1 if postseason else 0))

            row = cursor.fetchone()

            if row:
                return {
                    'player_id': row['player_id'],
                    'season': row['season'],
                    'games_played': row['games_played'],
                    'pts': row['pts'],
                    'reb': row['reb'],
                    'ast': row['ast'],
                    'fg_pct': row['fg_pct'],
                    'fg3_pct': row['fg3_pct'],
                    'ft_pct': row['ft_pct'],
                    'min': row['min']
                }

            return None

    def cache_game_stats(self, player_id: int, games: List[Dict], postseason: bool = False):
        """Cache game statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            for game in games:
                game_data = game.get('game', {})

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO game_stats
                    (player_id, game_id, game_date, season, postseason, pts, reb, ast, 
                     fg_pct, fg3m, min, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (player_id, game_data.get('id'), game_data.get('date'),
                     game_data.get('season'), 1 if postseason else 0, game.get('pts'), game.get('reb'),
                     game.get('ast'), game.get('fg_pct'), game.get('fg3m'),
                     game.get('min')))

            conn.commit()

    def get_game_stats(self,
                       player_id: int,
                       limit: int = 20,
                       season: int = None,
                       postseason: bool = False) -> List[Dict]:
        """Retrieve cached game stats"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if season is not None:
                cursor.execute(
                    """
                    SELECT * FROM game_stats 
                    WHERE player_id = ? AND season = ? AND postseason = ?
                    AND last_updated > datetime('now', '-1 day')
                    ORDER BY game_date DESC
                    LIMIT ?
                """, (player_id, season, 1 if postseason else 0, limit))
            else:
                cursor.execute(
                    """
                    SELECT * FROM game_stats 
                    WHERE player_id = ? AND postseason = ?
                    AND last_updated > datetime('now', '-1 day')
                    ORDER BY game_date DESC
                    LIMIT ?
                """, (player_id, 1 if postseason else 0, limit))

            rows = cursor.fetchall()

            return [{
                'game': {
                    'id': row['game_id'],
                    'date': row['game_date'],
                    'season': row['season']
                },
                'pts': row['pts'],
                'reb': row['reb'],
                'ast': row['ast'],
                'fg_pct': row['fg_pct'],
                'fg3m': row['fg3m'],
                'min': row['min']
            } for row in rows]

    def cache_league_averages(self, season: int, averages: Dict):
        """Cache league averages"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO league_averages
                (season, pts, reb, ast, fg_pct, fg3_pct, ft_pct, min,
                 pts_std, reb_std, ast_std, fg_pct_std, fg3_pct_std, ft_pct_std, min_std,
                 last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (season, averages.get('pts'), averages.get('reb'),
                  averages.get('ast'), averages.get('fg_pct'),
                  averages.get('fg3_pct'), averages.get('ft_pct'),
                  averages.get('min'), averages.get('pts_std'),
                  averages.get('reb_std'), averages.get('ast_std'),
                  averages.get('fg_pct_std'), averages.get('fg3_pct_std'),
                  averages.get('ft_pct_std'), averages.get('min_std')))

            conn.commit()

    def get_league_averages(self, season: int) -> Optional[Dict]:
        """Retrieve cached league averages"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM league_averages 
                WHERE season = ?
                AND last_updated > datetime('now', '-7 days')
            """, (season, ))

            row = cursor.fetchone()

            if row:
                return {
                    'pts': row['pts'],
                    'reb': row['reb'],
                    'ast': row['ast'],
                    'fg_pct': row['fg_pct'],
                    'fg3_pct': row['fg3_pct'],
                    'ft_pct': row['ft_pct'],
                    'min': row['min'],
                    'pts_std': row['pts_std'],
                    'reb_std': row['reb_std'],
                    'ast_std': row['ast_std'],
                    'fg_pct_std': row['fg_pct_std'],
                    'fg3_pct_std': row['fg3_pct_std'],
                    'ft_pct_std': row['ft_pct_std'],
                    'min_std': row['min_std']
                }

            return None

    def add_favorite(self, player_id: int, player_name: str):
        """Add player to favorites"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO favorites (player_id, player_name)
                VALUES (?, ?)
            """, (player_id, player_name))

            conn.commit()

    def remove_favorite(self, player_id: int):
        """Remove player from favorites"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM favorites WHERE player_id = ?",
                           (player_id, ))

            conn.commit()

    def get_favorites(self) -> List[Dict]:
        """Get all favorite players"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT f.player_id, f.player_name, p.team_abbreviation
                FROM favorites f
                LEFT JOIN players p ON f.player_id = p.id
                ORDER BY f.added_date DESC
            """)

            rows = cursor.fetchall()

            return [{
                'player_id': row['player_id'],
                'player_name': row['player_name'],
                'team_abbreviation': row['team_abbreviation'] or 'N/A'
            } for row in rows]

    def is_favorite(self, player_id: int) -> bool:
        """Check if player is in favorites"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM favorites WHERE player_id = ?",
                           (player_id, ))

            return cursor.fetchone() is not None

    def _player_row_to_dict(self, row) -> Dict:
        """Convert player row to dictionary"""
        return {
            'id': row['id'],
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'team': {
                'id': row['team_id'],
                'full_name': row['team_name'],
                'abbreviation': row['team_abbreviation']
            },
            'position': row['position'],
            'height_feet': row['height_feet'],
            'height_inches': row['height_inches'],
            'weight_pounds': row['weight_pounds']
        }

    def clear_old_cache(self, days: int = 30):
        """Clear cache entries older than specified days"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                DELETE FROM players 
                WHERE last_updated < datetime('now', '-{days} days')
            """)

            cursor.execute(f"""
                DELETE FROM season_stats 
                WHERE last_updated < datetime('now', '-{days} days')
            """)

            cursor.execute(f"""
                DELETE FROM game_stats 
                WHERE last_updated < datetime('now', '-{days} days')
            """)

            conn.commit()
    
    #  === Prediction Tracking Methods ===
    
    def save_prediction(self, player_id: int, player_name: str, game_date: str, 
                       season: int, stat_type: str, threshold: float, 
                       predicted_probability: float, confidence: str):
        """Save a prediction for future verification"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO predictions 
                (player_id, player_name, game_date, season, stat_type, threshold,
                 predicted_probability, prediction_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (player_id, player_name, game_date, season, stat_type, 
                  threshold, predicted_probability, confidence))
            
            conn.commit()
            return cursor.lastrowid
    
    def verify_prediction(self, prediction_id: int, actual_value: float):
        """Verify a prediction with actual game result"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get prediction details
            cursor.execute("""
                SELECT threshold, predicted_probability, stat_type
                FROM predictions
                WHERE id = ?
            """, (prediction_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            threshold = result['threshold']
            predicted_prob = result['predicted_probability']
            stat_type = result['stat_type']
            
            # Determine if prediction was correct
            actual_result = 1 if actual_value >= threshold else 0
            prediction_correct = 1 if (predicted_prob > 0.5 and actual_result == 1) or (predicted_prob <= 0.5 and actual_result == 0) else 0
            
            # Update prediction record
            cursor.execute("""
                UPDATE predictions
                SET actual_value = ?, actual_result = ?, prediction_correct = ?,
                    verified_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (actual_value, actual_result, prediction_correct, prediction_id))
            
            # Update prediction metrics
            self._update_prediction_metrics(stat_type, threshold, prediction_correct, cursor)
            
            conn.commit()
            return True
    
    def _update_prediction_metrics(self, stat_type: str, threshold: float, 
                                   prediction_correct: int, cursor):
        """Update aggregate prediction accuracy metrics"""
        # Determine threshold range
        if threshold < 10:
            threshold_range = "low"
        elif threshold < 20:
            threshold_range = "medium"
        else:
            threshold_range = "high"
        
        # Get current metrics
        cursor.execute("""
            SELECT total_predictions, correct_predictions
            FROM prediction_metrics
            WHERE stat_type = ? AND threshold_range = ?
        """, (stat_type, threshold_range))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing metrics
            total = row['total_predictions'] + 1
            correct = row['correct_predictions'] + prediction_correct
            accuracy = (correct / total) * 100 if total > 0 else 0.0
            
            cursor.execute("""
                UPDATE prediction_metrics
                SET total_predictions = ?, correct_predictions = ?,
                    accuracy_rate = ?, last_updated = CURRENT_TIMESTAMP
                WHERE stat_type = ? AND threshold_range = ?
            """, (total, correct, accuracy, stat_type, threshold_range))
        else:
            # Insert new metrics
            accuracy = (prediction_correct / 1) * 100
            cursor.execute("""
                INSERT INTO prediction_metrics
                (stat_type, threshold_range, total_predictions, correct_predictions, accuracy_rate)
                VALUES (?, ?, ?, ?, ?)
            """, (stat_type, threshold_range, 1, prediction_correct, accuracy))
    
    def get_prediction_accuracy(self, stat_type: str = None) -> List[Dict]:
        """Get prediction accuracy metrics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if stat_type:
                cursor.execute("""
                    SELECT * FROM prediction_metrics
                    WHERE stat_type = ?
                    ORDER BY threshold_range
                """, (stat_type,))
            else:
                cursor.execute("""
                    SELECT * FROM prediction_metrics
                    ORDER BY stat_type, threshold_range
                """)
            
            rows = cursor.fetchall()
            
            return [{
                'stat_type': row['stat_type'],
                'threshold_range': row['threshold_range'],
                'total_predictions': row['total_predictions'],
                'correct_predictions': row['correct_predictions'],
                'accuracy_rate': row['accuracy_rate'],
                'last_updated': row['last_updated']
            } for row in rows]
    
    def get_recent_predictions(self, player_id: int = None, limit: int = 20, 
                              verified_only: bool = False) -> List[Dict]:
        """Get recent predictions, optionally filtered by player"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM predictions WHERE 1=1"
            params = []
            
            if player_id:
                query += " AND player_id = ?"
                params.append(player_id)
            
            if verified_only:
                query += " AND verified_at IS NOT NULL"
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [{
                'id': row['id'],
                'player_id': row['player_id'],
                'player_name': row['player_name'],
                'game_date': row['game_date'],
                'season': row['season'],
                'stat_type': row['stat_type'],
                'threshold': row['threshold'],
                'predicted_probability': row['predicted_probability'],
                'prediction_confidence': row['prediction_confidence'],
                'actual_result': row['actual_result'],
                'actual_value': row['actual_value'],
                'prediction_correct': row['prediction_correct'],
                'created_at': row['created_at'],
                'verified_at': row['verified_at']
            } for row in rows]
    
    def get_unverified_predictions(self, cutoff_date: str = None) -> List[Dict]:
        """Get predictions that haven't been verified yet and are past their game date"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if cutoff_date:
                cursor.execute("""
                    SELECT * FROM predictions
                    WHERE verified_at IS NULL AND game_date <= ?
                    ORDER BY game_date DESC
                """, (cutoff_date,))
            else:
                cursor.execute("""
                    SELECT * FROM predictions
                    WHERE verified_at IS NULL AND game_date <= date('now')
                    ORDER BY game_date DESC
                """)
            
            rows = cursor.fetchall()
            
            return [{
                'id': row['id'],
                'player_id': row['player_id'],
                'player_name': row['player_name'],
                'game_date': row['game_date'],
                'season': row['season'],
                'stat_type': row['stat_type'],
                'threshold': row['threshold'],
                'predicted_probability': row['predicted_probability']
            } for row in rows]
