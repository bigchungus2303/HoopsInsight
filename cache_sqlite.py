"""
SQLite-backed cache with hard schema-versioning for NBA stats app.
Deterministic, persistent, auto-invalidating on schema mismatch.
"""

from __future__ import annotations
import sqlite3
import json
import time
import hashlib
from typing import Optional

# Constants
SCHEMA_VER = "games:v2"  # bump when fields change
REQUIRED_FIELDS = {"id", "date", "home_team_id", "visitor_team_id"}
DEFAULT_TTL_SECONDS = 6 * 3600  # 6 hours - shorten during dev
DB_PATH = "cache.db"
TABLE = "http_cache"


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize cache database with required schema and security settings."""
    conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    
    # Security: Limit cache size
    cursor.execute("PRAGMA max_page_count=50000")  # ~200MB limit
    
    # Create table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE}(
            key TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at INTEGER NOT NULL,
            schema_ver TEXT NOT NULL
        )
    """)
    
    # Create indices
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_http_cache_updated 
        ON {TABLE}(updated_at)
    """)
    
    cursor.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_http_cache_schema 
        ON {TABLE}(schema_ver)
    """)
    
    conn.commit()
    conn.close()


def cache_key(namespace: str, params: dict, schema_ver: str = SCHEMA_VER) -> str:
    """
    Generate deterministic cache key from namespace, params, and schema version.
    
    Args:
        namespace: Cache namespace (e.g., "balldontlie:games")
        params: Parameters dictionary
        schema_ver: Schema version string
    
    Returns:
        SHA256 hex digest
    """
    # Sort params for deterministic serialization
    sorted_params = json.dumps(params, sort_keys=True, separators=(',', ':'))
    
    # Combine namespace + schema + params
    canonical = f"{namespace}|{schema_ver}|{sorted_params}"
    
    # Hash
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def get_cached(
    key: str, 
    max_age_s: int = DEFAULT_TTL_SECONDS, 
    db_path: str = DB_PATH
) -> Optional[dict]:
    """
    Retrieve cached payload if valid.
    
    Args:
        key: Cache key
        max_age_s: Maximum age in seconds (TTL)
        db_path: Database path
    
    Returns:
        Cached dict or None if miss/expired/schema mismatch
    """
    conn = sqlite3.connect(db_path, timeout=5.0, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(
        f"SELECT payload, updated_at, schema_ver FROM {TABLE} WHERE key = ?",
        (key,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    payload_str, updated_at, cached_schema_ver = row
    
    # Check schema version
    if cached_schema_ver != SCHEMA_VER:
        return None
    
    # Check TTL
    now = int(time.time())
    if (now - updated_at) > max_age_s:
        return None
    
    # Deserialize and return
    try:
        return json.loads(payload_str)
    except json.JSONDecodeError:
        return None


def set_cached(
    key: str, 
    payload: dict, 
    schema_ver: str = SCHEMA_VER, 
    db_path: str = DB_PATH
) -> None:
    """
    Store payload in cache with current timestamp and schema version.
    
    Args:
        key: Cache key
        payload: Data to cache
        schema_ver: Schema version
        db_path: Database path
    """
    # Validate payload size (prevent cache bloat)
    payload_str = json.dumps(payload, separators=(',', ':'))
    if len(payload_str) > 5_000_000:  # 5MB limit per entry
        raise ValueError("Payload too large for caching")
    
    conn = sqlite3.connect(db_path, timeout=5.0, check_same_thread=False)
    cursor = conn.cursor()
    
    now = int(time.time())
    
    cursor.execute(
        f"""
        INSERT OR REPLACE INTO {TABLE} (key, payload, updated_at, schema_ver)
        VALUES (?, ?, ?, ?)
        """,
        (key, payload_str, now, schema_ver)
    )
    
    conn.commit()
    conn.close()


def clear_cache(db_path: str = DB_PATH) -> None:
    """Delete all cache entries."""
    conn = sqlite3.connect(db_path, timeout=5.0, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {TABLE}")
    
    # Vacuum to reclaim space
    cursor.execute("VACUUM")
    
    conn.commit()
    conn.close()


def validate_games_schema(games: list[dict]) -> None:
    """
    Validate that all games have required fields.
    
    Args:
        games: List of game dictionaries
    
    Raises:
        ValueError: If any game is missing required fields
    """
    for i, game in enumerate(games):
        if not REQUIRED_FIELDS.issubset(game.keys()):
            missing = REQUIRED_FIELDS - set(game.keys())
            raise ValueError(
                f"CACHE_SCHEMA_MISMATCH: Game {i} missing fields: {missing}"
            )


# Self-tests
def main():
    """Run self-tests for cache functionality."""
    import os
    import tempfile
    
    print("Running cache_sqlite.py self-tests...")
    
    # Use temporary database for tests
    test_db = os.path.join(tempfile.gettempdir(), "test_cache.db")
    
    # Clean up any existing test db
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Test 1: init_db
    print("\n[OK] Test 1: init_db()")
    init_db(test_db)
    assert os.path.exists(test_db), "Database file should exist"
    
    # Test 2: cache_key determinism
    print("[OK] Test 2: cache_key() determinism")
    params1 = {"player_id": 123, "season": 2024}
    params2 = {"season": 2024, "player_id": 123}  # Different order
    key1 = cache_key("test:namespace", params1)
    key2 = cache_key("test:namespace", params2)
    assert key1 == key2, "Keys should be identical regardless of param order"
    assert len(key1) == 64, "SHA256 should produce 64-char hex string"
    
    # Test 3: set_cached / get_cached round-trip
    print("[OK] Test 3: set_cached() / get_cached() round-trip")
    test_key = cache_key("test:games", {"season": 2024})
    test_payload = {"games": [{"id": 1, "score": 100}], "count": 1}
    set_cached(test_key, test_payload, db_path=test_db)
    retrieved = get_cached(test_key, db_path=test_db)
    assert retrieved == test_payload, "Payload should match"
    
    # Test 4: TTL expiry
    print("[OK] Test 4: TTL expiry behavior")
    expired_key = cache_key("test:expired", {"id": 999})
    set_cached(expired_key, {"data": "old"}, db_path=test_db)
    time.sleep(1)  # Wait for 1 second to ensure TTL can expire
    # Check with 0 second TTL - should return None
    result = get_cached(expired_key, max_age_s=0, db_path=test_db)
    assert result is None, "Expired cache should return None"
    
    # Test 5: Schema version mismatch
    print("[OK] Test 5: SCHEMA_VER mismatch behavior")
    mismatch_key = cache_key("test:schema", {"id": 1}, schema_ver="old:v1")
    set_cached(mismatch_key, {"data": "test"}, schema_ver="old:v1", db_path=test_db)
    # Try to retrieve with current SCHEMA_VER
    result = get_cached(mismatch_key, db_path=test_db)
    assert result is None, "Schema mismatch should return None"
    
    # Test 6: validate_games_schema
    print("[OK] Test 6: validate_games_schema()")
    valid_games = [
        {"id": 1, "date": "2024-01-01", "home_team_id": 10, "visitor_team_id": 20},
        {"id": 2, "date": "2024-01-02", "home_team_id": 15, "visitor_team_id": 25}
    ]
    validate_games_schema(valid_games)  # Should not raise
    
    invalid_games = [
        {"id": 1, "date": "2024-01-01"}  # Missing team IDs
    ]
    try:
        validate_games_schema(invalid_games)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "CACHE_SCHEMA_MISMATCH" in str(e)
    
    # Test 7: clear_cache
    print("[OK] Test 7: clear_cache()")
    clear_cache(test_db)
    result = get_cached(test_key, db_path=test_db)
    assert result is None, "Cache should be empty after clear"
    
    # Clean up
    os.remove(test_db)
    
    print("\n[SUCCESS] All tests passed!")


if __name__ == "__main__":
    main()

