"""
Health check endpoint for monitoring
"""
import os
import sqlite3

def check_health() -> dict:
    """
    Check application health status
    
    Returns:
        dict with status and details
    """
    health = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check cache database
    try:
        if os.path.exists("cache.db"):
            conn = sqlite3.connect("cache.db", timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            health["checks"]["cache_db"] = "ok"
        else:
            health["checks"]["cache_db"] = "missing"
            health["status"] = "degraded"
    except Exception as e:
        health["checks"]["cache_db"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check user database
    try:
        if os.path.exists("nba_cache.db"):
            conn = sqlite3.connect("nba_cache.db", timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            health["checks"]["user_db"] = "ok"
        else:
            health["checks"]["user_db"] = "missing"
            health["status"] = "degraded"
    except Exception as e:
        health["checks"]["user_db"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check data directory
    if os.path.exists("data") and os.access("data", os.W_OK):
        health["checks"]["data_dir"] = "ok"
    else:
        health["checks"]["data_dir"] = "not_writable"
        health["status"] = "degraded"
    
    return health

if __name__ == "__main__":
    import json
    result = check_health()
    print(json.dumps(result, indent=2))
    exit(0 if result["status"] == "healthy" else 1)

