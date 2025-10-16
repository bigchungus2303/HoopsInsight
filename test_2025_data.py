import os
import requests
from datetime import datetime

# API setup
API_KEY = os.getenv('NBA_API_KEY')
BASE_URL = "https://api.balldontlie.io"

# balldontlie uses direct API key in Authorization header
headers = {'Authorization': API_KEY} if API_KEY else {}

print(f"API Key present: {'Yes' if API_KEY else 'No'}")
if API_KEY:
    print(f"API Key format: {API_KEY[:20]}..." if len(API_KEY) > 20 else "API Key too short")

# Test popular players
test_players = {
    'LeBron James': 237,
    'Stephen Curry': 115,
    'Giannis Antetokounmpo': 15,
    'Kevin Durant': 140,
    'Luka Doncic': 246
}

print("=" * 60)
print("CHECKING 2025 NBA DATA AVAILABILITY")
print("=" * 60)

for name, player_id in test_players.items():
    print(f"\n🏀 {name} (ID: {player_id})")
    print("-" * 40)
    
    # Check season averages (regular season)
    url = f"{BASE_URL}/nba/v1/season_averages/general"
    params = {
        'season': 2025,
        'season_type': 'regular',
        'type': 'base',
        'player_ids[]': player_id,
        'per_page': 100
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', [])
            if data:
                stats = data[0]
                print(f"  ✅ Regular season stats: {stats.get('games_played', 0)} games, {stats.get('pts', 0):.1f} PPG")
            else:
                print(f"  ❌ No regular season stats for 2025")
        else:
            print(f"  ❌ API error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check recent games (regular season)
    url = f"{BASE_URL}/v1/stats"
    params = {
        'player_ids[]': player_id,
        'seasons[]': 2025,
        'season_types[]': 'regular',
        'per_page': 10
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            games = response.json().get('data', [])
            if games:
                print(f"  ✅ Regular season games: {len(games)} games found")
                latest_game = games[0].get('game', {}).get('date', 'Unknown')
                print(f"     Latest game date: {latest_game}")
            else:
                print(f"  ❌ No regular season games for 2025")
        else:
            print(f"  ❌ API error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check preseason games
    params['season_types[]'] = 'preseason'
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            games = response.json().get('data', [])
            if games:
                print(f"  ✅ Preseason games: {len(games)} games found")
                latest_game = games[0].get('game', {}).get('date', 'Unknown')
                print(f"     Latest preseason date: {latest_game}")
            else:
                print(f"  ❌ No preseason games for 2025")
        else:
            print(f"  ❌ API error: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
